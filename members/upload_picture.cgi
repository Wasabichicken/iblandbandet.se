#!/usr/bin/env python3

import hmac
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cgi
from avatars import fix_upload_permissions
from base_path import url
from dal.members import update_profile_picture
from layout import render
from session_auth import current_member

MAX_UPLOAD_BYTES = 3 * 1024 * 1024
JPEG_MAGIC = b'\xff\xd8\xff'
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'static', 'uploads', 'avatars')
UPLOAD_URL_PREFIX = '/static/uploads/avatars/'


def redirect_to_profile():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/members/profile.cgi')))
    print()


def error_page(member, message):
    render('error.mako', title='Fel — iBlandbandet', member=member, message=message)


def main():
    member, csrf_token = current_member()
    if member is None:
        redirect_to_profile()
        return

    content_length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    if content_length > MAX_UPLOAD_BYTES:
        error_page(member, 'Bilden är för stor.')
        return

    form = cgi.FieldStorage(fp=sys.stdin.buffer, environ=os.environ, keep_blank_values=True)

    if not hmac.compare_digest(form.getvalue('csrf_token', ''), csrf_token):
        error_page(member, 'Sessionen är ogiltig, ladda om sidan och försök igen.')
        return

    field = form['avatar'] if 'avatar' in form else None
    if field is None or not field.filename:
        error_page(member, 'Ingen bild valdes.')
        return

    data = field.file.read()
    if not data.startswith(JPEG_MAGIC):
        error_page(member, 'Bilden måste vara en JPEG.')
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
