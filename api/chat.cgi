#!/usr/bin/env python3

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cgi
from api_auth import current_api_member
from api_common import json_response, read_json_body
from avatars import fix_upload_permissions
from dal.chat import create_message, delete_message, get_message_by_id, list_messages
from htsecrets import get_secret

MAX_IMAGE_BYTES = 10 * 1024 * 1024
DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 100

# Sniffed from the file's own bytes rather than stored as a column - chat
# only has a small, known set of realistic phone-camera/screenshot formats,
# and this avoids a schema change just to remember what upload_picture.cgi
# already proves you can check for free at serve time (it does the same
# thing for its own single-format JPEG check).
IMAGE_SIGNATURES = (
    (b'\xff\xd8\xff', 'image/jpeg'),
    (b'\x89PNG\r\n\x1a\n', 'image/png'),
    (b'GIF87a', 'image/gif'),
    (b'GIF89a', 'image/gif'),
)


def detect_image_mime(data):
    if data[:12].startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'
    for signature, mime in IMAGE_SIGNATURES:
        if data.startswith(signature):
            return mime
    return None


def image_storage_path(image_uuid):
    # Same uppercase/lowercase normalization gotcha as drive.cgi's
    # storage_path(): psqlodbc hands UUID columns back uppercase, but files
    # are written to disk using str(uuid.uuid4())'s lowercase form.
    return os.path.join(os.environ['CHAT_ROOT'], str(image_uuid).lower())


def iso_utc(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None


def message_json(row):
    return {
        'id': row.id,
        'member_id': row.member_id,
        'body': row.body,
        # Lowercased for the same reason image_storage_path() lowercases:
        # psqlodbc hands UUID columns back uppercase, but the value was
        # originally generated lowercase (str(uuid.uuid4())) and stored on
        # disk that way - without normalizing here too, a message fetched
        # via list_messages() would show a differently-cased image_id than
        # the same message's own upload response did.
        'image_id': str(row.image_uuid).lower() if row.image_uuid else None,
        'created_at': iso_utc(row.created_at),
        'profile_picture': row.profile_picture,
    }


def trigger_broadcast(payload):
    # The live relay is a nice-to-have on top of a message that's already
    # durably saved (see CHAT.md's persist-then-broadcast ordering) - if
    # the Worker is unreachable or not yet configured, the request that
    # triggered this still succeeds; connected clients just won't see this
    # particular update live and will pick it up on their next history
    # fetch instead. Same graceful-degradation shape as DiceBear fetches
    # in avatars.py.
    url = os.environ.get('CHAT_BROADCAST_URL')
    secret = get_secret('CHAT_BROADCAST_SECRET')
    if not url or not secret:
        return
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            # Cloudflare's edge bot-protection blocks the default
            # "Python-urllib/3.6" User-Agent outright (HTTP 403, Cloudflare
            # error 1010) before the request ever reaches the Worker - caught
            # live via a one-off diagnostic script, since urlopen's
            # HTTPError is a URLError subclass and was being silently
            # swallowed below. Any non-default User-Agent clears it.
            headers={
                'Content-Type': 'application/json',
                'X-Broadcast-Secret': secret,
                'User-Agent': 'iblandbandet-chat-broadcast/1.0',
            },
            method='POST',
        )
        urllib.request.urlopen(request, timeout=5)
    except (urllib.error.URLError, OSError):
        pass


def handle_list(query):
    before_raw = query.get('before', [''])[0]
    before_id = int(before_raw) if before_raw.isdigit() else None

    limit_raw = query.get('limit', [''])[0]
    limit = int(limit_raw) if limit_raw.isdigit() else DEFAULT_LIST_LIMIT
    limit = max(1, min(limit, MAX_LIST_LIMIT))

    messages = list_messages(before_id=before_id, limit=limit)
    json_response('200 OK', [message_json(row) for row in messages])


def serve_image(image_id):
    file_path = image_storage_path(image_id)
    if not os.path.exists(file_path):
        json_response('404 Not Found', {'error': 'Bilden hittades inte.'})
        return

    with open(file_path, 'rb') as f:
        data = f.read()
    mime = detect_image_mime(data) or 'application/octet-stream'

    sys.stdout.write('Content-Type: {}\r\n'.format(mime))
    sys.stdout.write('Content-Length: {}\r\n'.format(len(data)))
    sys.stdout.write('\r\n')
    sys.stdout.flush()
    sys.stdout.buffer.write(data)


def handle_send(member, values):
    body = (values.get('body') or '').strip()
    if not body:
        json_response('400 Bad Request', {'error': 'body måste fyllas i.'})
        return

    message_id, created_at = create_message(member.id, body=body)
    payload = {'id': message_id, 'member_id': member.id, 'body': body,
               'image_id': None, 'created_at': iso_utc(created_at),
               'profile_picture': member.profile_picture}
    trigger_broadcast({'type': 'message', **payload})
    json_response('200 OK', payload)


def handle_delete(member, values):
    message_id = values.get('message_id')
    if not isinstance(message_id, int):
        json_response('400 Bad Request', {'error': 'Ogiltigt id.'})
        return

    message = get_message_by_id(message_id)
    if message is None:
        json_response('404 Not Found', {'error': 'Hittades inte.'})
        return
    if message.member_id != member.id and not member.is_admin:
        json_response('403 Forbidden', {'error': 'Du kan bara ta bort dina egna meddelanden.'})
        return

    if message.image_uuid:
        try:
            os.remove(image_storage_path(message.image_uuid))
        except OSError:
            pass
    delete_message(message_id)
    trigger_broadcast({'type': 'delete', 'id': message_id})
    json_response('200 OK', {'ok': True})


def handle_image_upload(member):
    content_length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    if content_length > MAX_IMAGE_BYTES:
        # Drain stdin before responding - Apache relays the request body
        # over a blocking pipe, and answering without reading it can
        # deadlock the connection, same as drive.cgi/upload_picture.cgi.
        remaining = content_length
        while remaining > 0:
            chunk = sys.stdin.buffer.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
        json_response('413 Payload Too Large', {'error': 'Bilden är för stor (max 10 MB).'})
        return

    form = cgi.FieldStorage(fp=sys.stdin.buffer, environ=os.environ, keep_blank_values=True)

    field = form['image'] if 'image' in form else None
    if field is None or not field.filename:
        json_response('400 Bad Request', {'error': 'Ingen bild valdes.'})
        return

    data = field.file.read()
    if detect_image_mime(data) is None:
        json_response('400 Bad Request', {'error': 'Filen är ingen känd bildtyp.'})
        return

    body = (form.getvalue('body', '') or '').strip() or None

    image_uuid = str(uuid.uuid4())
    os.makedirs(os.environ['CHAT_ROOT'], exist_ok=True)
    file_path = image_storage_path(image_uuid)
    with open(file_path, 'wb') as out:
        out.write(data)
    fix_upload_permissions(os.environ['CHAT_ROOT'], file_path)

    try:
        message_id, created_at = create_message(member.id, body=body, image_uuid=image_uuid,
                                                  image_size_bytes=len(data))
    except Exception:
        # Write succeeded but the DB insert didn't - clean up the orphaned
        # file rather than leaving it unreferenced (see CHAT.md's
        # atomic-upload reasoning).
        try:
            os.remove(file_path)
        except OSError:
            pass
        json_response('500 Internal Server Error', {'error': 'Meddelandet kunde inte sparas.'})
        return

    payload = {'id': message_id, 'member_id': member.id, 'body': body,
               'image_id': image_uuid, 'created_at': iso_utc(created_at),
               'profile_picture': member.profile_picture}
    trigger_broadcast({'type': 'message', **payload})
    json_response('200 OK', payload)


def main():
    member = current_api_member()
    if member is None:
        json_response('401 Unauthorized', {'error': 'Ogiltig eller saknad token.'})
        return

    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method == 'GET':
        query = parse_qs(os.environ.get('QUERY_STRING', ''))
        image_id = query.get('image', [''])[0]
        if image_id:
            serve_image(image_id)
        else:
            handle_list(query)
        return

    if method != 'POST':
        json_response('405 Method Not Allowed', {'error': 'GET eller POST krävs.'})
        return

    content_type = os.environ.get('CONTENT_TYPE', '')
    if content_type.startswith('multipart/form-data'):
        handle_image_upload(member)
        return

    values = read_json_body()
    action = values.get('action')
    if action == 'send':
        handle_send(member, values)
    elif action == 'delete':
        handle_delete(member, values)
    else:
        json_response('400 Bad Request', {'error': 'Okänd åtgärd.'})


if __name__ == '__main__':
    main()
