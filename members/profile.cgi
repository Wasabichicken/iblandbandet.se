#!/usr/bin/env python3

import hmac
import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from dal.members import DuplicateEmailError, update_password, update_profile, update_profile_picture, verify_password
from layout import render
from session_auth import current_member

UPLOAD_URL_PREFIX = '/static/uploads/avatars/'
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'static', 'uploads', 'avatars')


def redirect_to_home():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print()


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    values = {key: parsed.get(key, [''])[0] for key in
              ('action', 'csrf_token', 'email', 'instruments', 'description',
               'current_password', 'new_password', 'confirm_password')}
    values['is_active'] = 'is_active' in parsed
    return values


def render_page(member, csrf_token, profile_message=None, profile_kind=None,
                 password_message=None, password_kind=None, picture_message=None, picture_kind=None,
                 profile_values=None):
    profile_values = profile_values or {
        'email': member.email,
        'instruments': member.instruments or '',
        'description': member.description or '',
        'is_active': member.is_active,
    }
    render(
        'profile.mako',
        title='Min profil — (i)Blandbandet',
        member=member,
        csrf_token=csrf_token,
        profile_message=profile_message,
        profile_kind=profile_kind,
        password_message=password_message,
        password_kind=password_kind,
        picture_message=picture_message,
        picture_kind=picture_kind,
        profile_values=profile_values,
        is_uploaded_photo=bool(member.profile_picture),
    )


def handle_update_profile(member, values):
    email = values['email'].strip()
    instruments = values['instruments'].strip() or None
    description = values['description'].strip() or None
    is_active = values['is_active']

    profile_values = {'email': email, 'instruments': values['instruments'],
                       'description': values['description'], 'is_active': is_active}

    if not email:
        return 'E-post måste fyllas i.', 'error', profile_values

    try:
        update_profile(member.id, email, instruments, description, is_active)
    except DuplicateEmailError:
        return 'Det finns redan en medlem med den e-postadressen.', 'error', profile_values

    return 'Uppgifterna har sparats.', 'success', profile_values


def handle_change_password(member, values):
    if not verify_password(values['current_password'], member.password_salt,
                             member.password_hash, member.password_iterations):
        return 'Fel nuvarande lösenord.', 'error'

    if not values['new_password']:
        return 'Nytt lösenord måste fyllas i.', 'error'

    if values['new_password'] != values['confirm_password']:
        return 'Lösenorden stämmer inte överens.', 'error'

    update_password(member.id, values['new_password'])
    return 'Lösenordet har bytts.', 'success'


def handle_remove_picture(member):
    old_url = member.profile_picture
    update_profile_picture(member.id, None)
    if old_url and old_url.startswith(UPLOAD_URL_PREFIX):
        old_path = os.path.join(UPLOAD_DIR, old_url[len(UPLOAD_URL_PREFIX):])
        try:
            os.remove(old_path)
        except OSError:
            pass
    return 'Profilbilden har tagits bort.', 'success'


def main():
    member, csrf_token = current_member()
    if member is None:
        redirect_to_home()
        return

    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        render_page(member, csrf_token)
        return

    values = read_form()

    if not hmac.compare_digest(values['csrf_token'], csrf_token):
        render_page(member, csrf_token, profile_message='Sessionen är ogiltig, ladda om sidan.',
                    profile_kind='error')
        return

    profile_message = profile_kind = password_message = password_kind = None
    picture_message = picture_kind = None
    profile_values = None

    if values['action'] == 'update_profile':
        profile_message, profile_kind, profile_values = handle_update_profile(member, values)
        member, csrf_token = current_member()
    elif values['action'] == 'change_password':
        password_message, password_kind = handle_change_password(member, values)
    elif values['action'] == 'remove_picture':
        picture_message, picture_kind = handle_remove_picture(member)
        member, csrf_token = current_member()

    render_page(member, csrf_token, profile_message, profile_kind, password_message, password_kind,
                picture_message, picture_kind, profile_values)


if __name__ == '__main__':
    main()
