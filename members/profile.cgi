#!/usr/bin/env python3

import hmac
import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from avatars import UPLOAD_DIR, UPLOAD_URL_PREFIX, generate_and_save_initials_avatar
from base_path import url
from dal.members import (DuplicateEmailError, count_admins, delete_member, update_password,
                          update_profile, update_profile_picture, verify_password)
from layout import render
from session_auth import current_member


def redirect_to_home():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print()


def redirect_after_account_deletion():
    # Mirrors logout.cgi's cookie-clearing exactly - the underlying session
    # row is already gone (iblandbandet_sessions cascades on member delete),
    # but clearing the cookie client-side too is still the right hygiene.
    is_https = os.environ.get('HTTPS') == 'on'
    secure = ' Secure;' if is_https else ''
    same_site = 'None' if is_https else 'Lax'
    print('Status: 302 Found')
    print('Location: {}?account_deleted=1'.format(url('/')))
    print('Set-Cookie: session=; Path=/; HttpOnly;{} SameSite={}; Max-Age=0'.format(secure, same_site))
    print()


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    values = {key: parsed.get(key, [''])[0] for key in
              ('action', 'csrf_token', 'email', 'instruments', 'description', 'name',
               'current_password', 'new_password', 'confirm_password')}
    values['is_active'] = 'is_active' in parsed
    return values


def render_page(member, csrf_token, profile_message=None, profile_kind=None,
                 password_message=None, password_kind=None, picture_message=None, picture_kind=None,
                 profile_values=None, confirm_delete=False, delete_message=None, delete_kind=None):
    profile_values = profile_values or {
        'email': member.email,
        'instruments': member.instruments or '',
        'description': member.description or '',
        'is_active': member.is_active,
        'name': member.name or '',
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
        confirm_delete=confirm_delete,
        delete_message=delete_message,
        delete_kind=delete_kind,
    )


def handle_update_profile(member, values):
    email = values['email'].strip()
    instruments = values['instruments'].strip() or None
    description = values['description'].strip() or None
    is_active = values['is_active']
    name = values['name'].strip() or None

    profile_values = {'email': email, 'instruments': values['instruments'],
                       'description': values['description'], 'is_active': is_active,
                       'name': values['name']}

    if not email:
        return 'E-post måste fyllas i.', 'error', profile_values

    try:
        update_profile(member.id, email, instruments, description, is_active, name)
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
    # Delete the old file *before* generating the replacement - the
    # regenerated avatar is saved under the exact same <id>_initials.svg
    # name a previously-generated one would already have, so doing this in
    # the other order would delete the fresh file we just wrote instead of
    # the stale one.
    if old_url and old_url.startswith(UPLOAD_URL_PREFIX):
        old_path = os.path.join(UPLOAD_DIR, old_url[len(UPLOAD_URL_PREFIX):])
        try:
            os.remove(old_path)
        except OSError:
            pass
    # Regenerate this member's DiceBear avatar rather than falling back to
    # the generic _default.svg - deterministic from their email, so this is
    # always "their" avatar, not a new random one. Falls back to NULL (the
    # generic silhouette) only if DiceBear can't be reached right now.
    picture_url = generate_and_save_initials_avatar(member.id, member.email)
    update_profile_picture(member.id, picture_url)
    return 'Profilbilden har tagits bort.', 'success'


def handle_delete_account(member, values):
    """Returns an error message, or None on success (account is already gone)."""
    if not verify_password(values['current_password'], member.password_salt,
                            member.password_hash, member.password_iterations):
        return 'Fel lösenord.'

    if member.is_admin and count_admins() <= 1:
        return ('Du är den enda administratören och kan inte radera ditt konto just nu - '
                'gör någon annan till administratör först.')

    # Same cleanup as admin.cgi's handle_delete_member(): the database row
    # going away doesn't take the uploaded/generated avatar file with it.
    if member.profile_picture and member.profile_picture.startswith(UPLOAD_URL_PREFIX):
        old_path = os.path.join(UPLOAD_DIR, member.profile_picture[len(UPLOAD_URL_PREFIX):])
        try:
            os.remove(old_path)
        except OSError:
            pass

    delete_member(member.id)
    return None


def main():
    member, csrf_token = current_member()
    if member is None:
        redirect_to_home()
        return

    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        query = parse_qs(os.environ.get('QUERY_STRING', ''))
        render_page(member, csrf_token, confirm_delete='confirm_delete' in query)
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
    elif values['action'] == 'delete_account':
        error = handle_delete_account(member, values)
        if error:
            render_page(member, csrf_token, confirm_delete=True, delete_message=error, delete_kind='error')
            return
        redirect_after_account_deletion()
        return

    render_page(member, csrf_token, profile_message, profile_kind, password_message, password_kind,
                picture_message, picture_kind, profile_values)


if __name__ == '__main__':
    main()
