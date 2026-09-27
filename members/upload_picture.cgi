#!/usr/bin/env python3

import hmac
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cgi
from avatars import UPLOAD_DIR, UPLOAD_URL_PREFIX, fix_upload_permissions
from base_path import url
from dal.members import update_profile_picture
from layout import render
from session_auth import current_member

MAX_UPLOAD_BYTES = 3 * 1024 * 1024
JPEG_MAGIC = b'\xff\xd8\xff'


def redirect_to_profile():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/members/profile.cgi')))
    print()


def error_page(member, status, message):
    print('Status: {}'.format(status))
    sys.stdout.flush()
    render('error.mako', title='Fel — (i)Blandbandet', member=member, message=message)


def main():
    member, csrf_token = current_member()
    if member is None:
        redirect_to_profile()
        return

    content_length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    if content_length > MAX_UPLOAD_BYTES:
        # Apache relays the request body to this script's stdin over a
        # blocking pipe - responding without reading it can deadlock the
        # connection (the client sits stuck trying to send bytes nobody is
        # draining), so the body must be discarded before we respond.
        remaining = content_length
        while remaining > 0:
            chunk = sys.stdin.buffer.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
        error_page(member, '413 Payload Too Large', 'Bilden är för stor.')
        return

    form = cgi.FieldStorage(fp=sys.stdin.buffer, environ=os.environ, keep_blank_values=True)

    if not hmac.compare_digest(form.getvalue('csrf_token', ''), csrf_token):
        error_page(member, '403 Forbidden', 'Sessionen är ogiltig, ladda om sidan och försök igen.')
        return

    field = form['avatar'] if 'avatar' in form else None
    if field is None or not field.filename:
        error_page(member, '400 Bad Request', 'Ingen bild valdes.')
        return

    data = field.file.read()
    if not data.startswith(JPEG_MAGIC):
        error_page(member, '400 Bad Request', 'Bilden måste vara en JPEG.')
        return

    old_url = member.profile_picture
    filename = '{}_{}.jpg'.format(member.id, secrets.token_hex(8))
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, 'wb') as out:
        out.write(data)
    fix_upload_permissions(UPLOAD_DIR, file_path)

    update_profile_picture(member.id, UPLOAD_URL_PREFIX + filename)

    if old_url and old_url.startswith(UPLOAD_URL_PREFIX):
        old_path = os.path.join(UPLOAD_DIR, old_url[len(UPLOAD_URL_PREFIX):])
        try:
            os.remove(old_path)
        except OSError:
            pass

    redirect_to_profile()


if __name__ == '__main__':
    main()
