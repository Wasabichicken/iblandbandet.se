#!/usr/bin/env python3

import hmac
import os
import sys
import uuid
from urllib.parse import parse_qs, quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cgi
from avatars import fix_upload_permissions
from base_path import url
from dal.drive import (create_directory, create_file, delete_item, get_item_by_id, list_children,
                        list_subdirectories, move_item, rename_item, set_owner)
from dal.members import get_member_by_id, list_all_members
from layout import render
from session_auth import current_member

MAX_UPLOAD_BYTES = 50 * 1024 * 1024

DEFAULT_FILE_TYPE = {
    'mime': 'application/octet-stream', 'icon': 'bi-file-earmark',
    'color_class': 'scores-icon-mscz', 'inline': False,
}
FILE_TYPES = {
    '.pdf': {'mime': 'application/pdf', 'icon': 'bi-file-earmark-pdf',
             'color_class': 'scores-icon-pdf', 'inline': True},
    '.txt': {'mime': 'text/plain; charset=utf-8', 'icon': 'bi-file-earmark-text',
              'color_class': 'scores-icon-text', 'inline': True},
    '.svg': {'mime': 'image/svg+xml', 'icon': 'bi-file-earmark-image',
             'color_class': 'drive-icon-image', 'inline': True},
    '.png': {'mime': 'image/png', 'icon': 'bi-file-earmark-image',
             'color_class': 'drive-icon-image', 'inline': True},
    '.mp3': {'mime': 'audio/mpeg', 'icon': 'bi-file-earmark-music',
             'color_class': 'scores-icon-audio', 'inline': True},
    '.eps': {'mime': 'application/postscript', 'icon': 'bi-file-earmark',
             'color_class': 'scores-icon-mscz', 'inline': False},
}

SWEDISH_MONTHS = (
    'jan', 'feb', 'mar', 'apr', 'maj', 'jun',
    'jul', 'aug', 'sep', 'okt', 'nov', 'dec',
)


def format_date(dt):
    return '{} {} {}'.format(dt.day, SWEDISH_MONTHS[dt.month - 1], dt.year)


def format_size(num_bytes):
    if num_bytes < 1000:
        return '{} B'.format(num_bytes)
    for unit in ('kB', 'MB', 'GB'):
        num_bytes /= 1000.0
        if num_bytes < 1000 or unit == 'GB':
            return '{} {}'.format(str(round(num_bytes, 1)).replace('.', ','), unit)


def get_file_type(name):
    ext = os.path.splitext(name)[1].lower()
    return FILE_TYPES.get(ext, DEFAULT_FILE_TYPE)


def parse_id(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def redirect_to_home():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print()


def redirect_to_listing(dir_id):
    print('Status: 302 Found')
    if dir_id is None:
        print('Location: {}'.format(url('/members/drive.cgi')))
    else:
        print('Location: {}'.format(url('/members/drive.cgi?dir={}'.format(dir_id))))
    print()


def error_page(member, status, message):
    # print() buffers through sys.stdout's own text layer, while render()
    # writes bytes straight to sys.stdout.buffer beneath it - without an
    # explicit flush here, the two can reach the underlying stream out of
    # order, so this "Status:" line arrives after render()'s output instead
    # of before it, and the CGI response ends up 200 OK instead of `status`.
    print('Status: {}'.format(status))
    sys.stdout.flush()
    render('error.mako', title='{} — (i)Blandbandet'.format(message), member=member, message=message)


def can_manage(member, item):
    # Admins can rename/move/delete any item, not just their own - the
    # ownership check everywhere else in this file always goes through this
    # single function so the admin bypass can't be forgotten in one spot.
    return item.owner_id == member.id or member.is_admin


def build_breadcrumb(dir_id):
    crumbs = []
    current_id = dir_id
    while current_id is not None:
        item = get_item_by_id(current_id)
        if item is None:
            break
        crumbs.append({'id': item.id, 'name': item.name})
        current_id = item.parent_id
    crumbs.reverse()
    for i, crumb in enumerate(crumbs):
        crumb['is_current'] = i == len(crumbs) - 1
    return crumbs


def is_descendant_or_self(candidate_id, ancestor_id):
    current_id = candidate_id
    while current_id is not None:
        if current_id == ancestor_id:
            return True
        item = get_item_by_id(current_id)
        if item is None:
            break
        current_id = item.parent_id
    return False


def describe_entry(row):
    file_type = None if row.is_directory else get_file_type(row.name)
    return {
        'id': row.id,
        'owner_id': row.owner_id,
        'name': row.name,
        'is_directory': row.is_directory,
        'icon': 'bi-folder-fill' if row.is_directory else file_type['icon'],
        'color_class': 'scores-icon-folder' if row.is_directory else file_type['color_class'],
        'ext': None if row.is_directory else os.path.splitext(row.name)[1].lower().lstrip('.'),
        'size': None if row.is_directory else format_size(row.size_bytes),
        'created': format_date(row.created_at),
        'created_iso': row.created_at.isoformat(),
        'profile_picture': row.profile_picture,
    }


def storage_path(storage_uuid):
    # psqlodbc hands UUID columns back in uppercase, but files are written to
    # disk using str(uuid.uuid4())'s lowercase form - normalize here so a
    # round-trip through the database doesn't change the case Linux's
    # case-sensitive filesystem needs to match.
    return os.path.join(os.environ['DRIVE_ROOT'], str(storage_uuid).lower())


def serve_file(member, item):
    file_type = get_file_type(item.name)
    file_path = storage_path(item.storage_uuid)
    if not os.path.exists(file_path):
        error_page(member, '404 Not Found', 'Filen hittades inte.')
        return

    ascii_name = item.name.encode('ascii', 'replace').decode('ascii')
    disposition = 'inline' if file_type['inline'] else 'attachment'
    sys.stdout.write('Content-Type: {}\r\n'.format(file_type['mime']))
    sys.stdout.write('Content-Length: {}\r\n'.format(os.path.getsize(file_path)))
    sys.stdout.write('Content-Disposition: {}; filename="{}"; filename*=UTF-8\'\'{}\r\n'.format(
        disposition, ascii_name, quote(item.name)))
    sys.stdout.write('\r\n')
    sys.stdout.flush()
    with open(file_path, 'rb') as f:
        sys.stdout.buffer.write(f.read())


def render_listing(member, csrf_token, dir_id, message=None, message_kind=None, confirm_delete=None,
                    rename_target=None, move_picker=None, change_owner_target=None):
    entries = [describe_entry(row) for row in list_children(dir_id)]
    parent_dir_id = None
    if dir_id is not None:
        current_dir = get_item_by_id(dir_id)
        if current_dir is not None:
            parent_dir_id = current_dir.parent_id
    render(
        'drive.mako',
        title='Filer — (i)Blandbandet',
        member=member,
        csrf_token=csrf_token,
        dir_id=dir_id,
        parent_dir_id=parent_dir_id,
        breadcrumb=build_breadcrumb(dir_id),
        entries=entries,
        message=message,
        message_kind=message_kind,
        confirm_delete=confirm_delete,
        rename_target=rename_target,
        move_picker=move_picker,
        change_owner_target=change_owner_target,
        all_members=list_all_members() if change_owner_target is not None else None,
    )


def handle_create_folder(member, form):
    parent_id = parse_id(form.getvalue('parent_id', ''))
    name = form.getvalue('name', '').strip()
    if not name:
        return 'Mappen måste ha ett namn.', 'error'
    if parent_id is not None:
        parent = get_item_by_id(parent_id)
        if parent is None or not parent.is_directory:
            return 'Mappen hittades inte.', 'error'
    create_directory(name, parent_id, member.id)
    return None, None


def handle_upload(member, form):
    parent_id = parse_id(form.getvalue('parent_id', ''))
    if parent_id is not None:
        parent = get_item_by_id(parent_id)
        if parent is None or not parent.is_directory:
            return 'Mappen hittades inte.', 'error'

    field = form['file'] if 'file' in form else None
    if field is None or not field.filename:
        return 'Ingen fil valdes.', 'error'

    name = os.path.basename(field.filename)
    data = field.file.read()

    storage_uuid = str(uuid.uuid4())
    os.makedirs(os.environ['DRIVE_ROOT'], exist_ok=True)
    file_path = storage_path(storage_uuid)
    with open(file_path, 'wb') as out:
        out.write(data)
    fix_upload_permissions(os.environ['DRIVE_ROOT'], file_path)

    try:
        create_file(name, parent_id, member.id, storage_uuid, len(data))
    except Exception:
        # Write succeeded but the DB insert didn't - clean up the orphaned
        # file and abort rather than leaving a dangling reference.
        try:
            os.remove(file_path)
        except OSError:
            pass
        return 'Filen kunde inte sparas.', 'error'

    return None, None


def handle_delete(member, item_id):
    item = get_item_by_id(item_id)
    if item is None:
        return 'Hittades inte.', 'error', None
    if not can_manage(member, item):
        return 'Du kan bara ta bort dina egna filer och mappar.', 'error', item.parent_id
    if item.is_directory and list_children(item.id):
        return 'Mappen är inte tom.', 'error', item.parent_id

    # Delete the database row first; if the file unlink below fails, the
    # member still sees success (the item is genuinely gone either way) and
    # the leftover bytes are cleaned up by hand later, not surfaced here.
    delete_item(item.id)
    if not item.is_directory:
        try:
            os.remove(storage_path(item.storage_uuid))
        except OSError:
            pass
    return None, None, item.parent_id


def handle_rename(member, item_id, name):
    item = get_item_by_id(item_id)
    if item is None:
        return 'Hittades inte.', 'error'
    if not can_manage(member, item):
        return 'Du kan bara byta namn på dina egna filer och mappar.', 'error'
    name = name.strip()
    if not name:
        return 'Namnet får inte vara tomt.', 'error'
    rename_item(item.id, name)
    return None, None


def handle_move(member, item_id, new_parent_id):
    item = get_item_by_id(item_id)
    if item is None:
        return 'Hittades inte.', 'error'
    if not can_manage(member, item):
        return 'Du kan bara flytta dina egna filer och mappar.', 'error'

    if new_parent_id is not None:
        destination = get_item_by_id(new_parent_id)
        if destination is None or not destination.is_directory:
            return 'Mappen hittades inte.', 'error'
        if item.is_directory and is_descendant_or_self(new_parent_id, item.id):
            return 'Du kan inte flytta en mapp in i sig själv.', 'error'

    move_item(item.id, new_parent_id)
    return None, None


def handle_copy(member, item_id):
    item = get_item_by_id(item_id)
    if item is None or item.is_directory:
        return 'Hittades inte.', 'error'

    # Deliberately no ownership check - any member can copy any file, since
    # copying only needs read access, which every member already has for
    # everything in the drive. The copy belongs to whoever clicked copy.
    source_path = storage_path(item.storage_uuid)
    with open(source_path, 'rb') as f:
        data = f.read()

    base, ext = os.path.splitext(item.name)
    new_name = '{} (kopia){}'.format(base, ext)
    new_storage_uuid = str(uuid.uuid4())
    file_path = storage_path(new_storage_uuid)
    with open(file_path, 'wb') as out:
        out.write(data)
    fix_upload_permissions(os.environ['DRIVE_ROOT'], file_path)

    try:
        create_file(new_name, item.parent_id, member.id, new_storage_uuid, len(data))
    except Exception:
        try:
            os.remove(file_path)
        except OSError:
            pass
        return 'Kopian kunde inte sparas.', 'error'

    return None, None


def handle_change_owner(member, item_id, new_owner_id):
    if not member.is_admin:
        return 'Endast administratörer kan byta ägare.', 'error'
    item = get_item_by_id(item_id)
    if item is None:
        return 'Hittades inte.', 'error'
    new_owner = get_member_by_id(new_owner_id) if new_owner_id is not None else None
    if new_owner is None:
        return 'Medlemmen hittades inte.', 'error'
    set_owner(item.id, new_owner.id)
    return None, None


def build_move_picker(item, picker_dir_id):
    if picker_dir_id is not None and item.is_directory and is_descendant_or_self(picker_dir_id, item.id):
        # Someone navigated the picker into the moved directory's own subtree
        # (a hand-edited URL, most likely) - reset to root rather than error.
        picker_dir_id = None
    folders = [
        {'id': folder.id, 'name': folder.name}
        for folder in list_subdirectories(picker_dir_id)
        if not (item.is_directory and is_descendant_or_self(folder.id, item.id))
    ]
    return {
        'item': item,
        'picker_dir_id': picker_dir_id,
        'breadcrumb': build_breadcrumb(picker_dir_id),
        'folders': folders,
    }


def main():
    member, csrf_token = current_member()
    if member is None:
        redirect_to_home()
        return

    if not os.environ.get('DRIVE_ROOT'):
        error_page(member, '500 Internal Server Error', 'Filarkivet är inte konfigurerat.')
        return

    if os.environ.get('REQUEST_METHOD', 'GET') == 'POST':
        content_length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
        if content_length > MAX_UPLOAD_BYTES:
            # Apache relays the request body to this script's stdin over a
            # blocking pipe - responding without reading it can deadlock the
            # connection (the client sits stuck trying to send bytes nobody
            # is draining), so the body must be discarded before we respond.
            remaining = content_length
            while remaining > 0:
                chunk = sys.stdin.buffer.read(min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
            error_page(member, '413 Payload Too Large', 'Filen är för stor (max 50 MB).')
            return

        form = cgi.FieldStorage(fp=sys.stdin.buffer, environ=os.environ, keep_blank_values=True)

        if not hmac.compare_digest(form.getvalue('csrf_token', ''), csrf_token):
            error_page(member, '403 Forbidden', 'Sessionen är ogiltig, ladda om sidan.')
            return

        action = form.getvalue('action', '')
        parent_id = parse_id(form.getvalue('parent_id', ''))

        if action == 'create_folder':
            message, kind = handle_create_folder(member, form)
            if kind == 'error':
                render_listing(member, csrf_token, parent_id, message=message, message_kind=kind)
                return
            redirect_to_listing(parent_id)
            return

        if action == 'upload':
            message, kind = handle_upload(member, form)
            if kind == 'error':
                render_listing(member, csrf_token, parent_id, message=message, message_kind=kind)
                return
            redirect_to_listing(parent_id)
            return

        if action == 'delete':
            item_id = parse_id(form.getvalue('item_id', ''))
            if item_id is None:
                redirect_to_listing(None)
                return
            message, kind, item_parent_id = handle_delete(member, item_id)
            if kind == 'error':
                render_listing(member, csrf_token, item_parent_id, message=message, message_kind=kind)
                return
            redirect_to_listing(item_parent_id)
            return

        if action == 'rename':
            item_id = parse_id(form.getvalue('item_id', ''))
            return_dir = parse_id(form.getvalue('dir', ''))
            if item_id is None:
                redirect_to_listing(return_dir)
                return
            message, kind = handle_rename(member, item_id, form.getvalue('name', ''))
            if kind == 'error':
                render_listing(member, csrf_token, return_dir, message=message, message_kind=kind,
                                rename_target=get_item_by_id(item_id))
                return
            redirect_to_listing(return_dir)
            return

        if action == 'move':
            item_id = parse_id(form.getvalue('item_id', ''))
            new_parent_id = parse_id(form.getvalue('new_parent_id', ''))
            return_dir = parse_id(form.getvalue('dir', ''))
            if item_id is None:
                redirect_to_listing(return_dir)
                return
            message, kind = handle_move(member, item_id, new_parent_id)
            if kind == 'error':
                item = get_item_by_id(item_id)
                picker = build_move_picker(item, new_parent_id) if (
                    item is not None and can_manage(member, item)) else None
                render_listing(member, csrf_token, return_dir, message=message, message_kind=kind,
                                move_picker=picker)
                return
            redirect_to_listing(return_dir)
            return

        if action == 'copy':
            item_id = parse_id(form.getvalue('item_id', ''))
            return_dir = parse_id(form.getvalue('dir', ''))
            if item_id is None:
                redirect_to_listing(return_dir)
                return
            message, kind = handle_copy(member, item_id)
            if kind == 'error':
                render_listing(member, csrf_token, return_dir, message=message, message_kind=kind)
                return
            redirect_to_listing(return_dir)
            return

        if action == 'change_owner':
            item_id = parse_id(form.getvalue('item_id', ''))
            new_owner_id = parse_id(form.getvalue('new_owner_id', ''))
            return_dir = parse_id(form.getvalue('dir', ''))
            if item_id is None:
                redirect_to_listing(return_dir)
                return
            message, kind = handle_change_owner(member, item_id, new_owner_id)
            if kind == 'error':
                render_listing(member, csrf_token, return_dir, message=message, message_kind=kind,
                                change_owner_target=get_item_by_id(item_id))
                return
            redirect_to_listing(return_dir)
            return

        redirect_to_listing(None)
        return

    query = parse_qs(os.environ.get('QUERY_STRING', ''))

    download_id = parse_id(query.get('download', [''])[0])
    if download_id is not None:
        item = get_item_by_id(download_id)
        if item is None or item.is_directory:
            error_page(member, '404 Not Found', 'Filen hittades inte.')
            return
        serve_file(member, item)
        return

    dir_id = parse_id(query.get('dir', [''])[0])
    if dir_id is not None:
        current_dir = get_item_by_id(dir_id)
        if current_dir is None or not current_dir.is_directory:
            error_page(member, '404 Not Found', 'Mappen hittades inte.')
            return

    confirm_delete_id = parse_id(query.get('confirm_delete', [''])[0])
    if confirm_delete_id is not None:
        target = get_item_by_id(confirm_delete_id)
        render_listing(member, csrf_token, dir_id, confirm_delete=target)
        return

    rename_id = parse_id(query.get('rename', [''])[0])
    if rename_id is not None:
        target = get_item_by_id(rename_id)
        if target is None or not can_manage(member, target):
            render_listing(member, csrf_token, dir_id, message='Hittades inte.', message_kind='error')
            return
        render_listing(member, csrf_token, dir_id, rename_target=target)
        return

    move_id = parse_id(query.get('move', [''])[0])
    if move_id is not None:
        item = get_item_by_id(move_id)
        if item is None or not can_manage(member, item):
            render_listing(member, csrf_token, dir_id, message='Hittades inte.', message_kind='error')
            return
        picker_dir_id = parse_id(query.get('picker_dir', [''])[0])
        render_listing(member, csrf_token, dir_id, move_picker=build_move_picker(item, picker_dir_id))
        return

    change_owner_id = parse_id(query.get('change_owner', [''])[0])
    if change_owner_id is not None:
        if not member.is_admin:
            render_listing(member, csrf_token, dir_id, message='Hittades inte.', message_kind='error')
            return
        target = get_item_by_id(change_owner_id)
        if target is None:
            render_listing(member, csrf_token, dir_id, message='Hittades inte.', message_kind='error')
            return
        render_listing(member, csrf_token, dir_id, change_owner_target=target)
        return

    render_listing(member, csrf_token, dir_id)


if __name__ == '__main__':
    main()
