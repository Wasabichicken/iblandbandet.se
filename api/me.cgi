#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_auth import current_api_member, get_bearer_token
from api_common import json_response, read_json_body
from avatars import api_avatar_url
from dal.api_tokens import delete_other_api_tokens
from dal.members import DuplicateEmailError, update_password, update_profile, verify_password


def member_json(member):
    return {
        'id': member.id,
        'email': member.email,
        'instruments': member.instruments,
        'description': member.description,
        'is_active': member.is_active,
        'is_admin': member.is_admin,
        'profile_picture': api_avatar_url(member.profile_picture),
        'name': member.name,
    }


def handle_update_profile(member, values):
    email = (values.get('email') or '').strip()
    if not email:
        json_response('400 Bad Request', {'error': 'E-post måste fyllas i.'})
        return

    instruments = (values.get('instruments') or '').strip() or None
    description = (values.get('description') or '').strip() or None
    is_active = bool(values.get('is_active', member.is_active))
    name = (values.get('name') or '').strip() or None

    try:
        update_profile(member.id, email, instruments, description, is_active, name)
    except DuplicateEmailError:
        json_response('409 Conflict', {'error': 'Det finns redan en medlem med den e-postadressen.'})
        return

    json_response('200 OK', member_json(current_api_member()))


def handle_change_password(member, token, values):
    current_password = values.get('current_password') or ''
    new_password = values.get('new_password') or ''

    if not verify_password(current_password, member.password_salt, member.password_hash,
                            member.password_iterations):
        json_response('401 Unauthorized', {'error': 'Fel nuvarande lösenord.'})
        return

    if not new_password:
        json_response('400 Bad Request', {'error': 'Nytt lösenord måste fyllas i.'})
        return

    update_password(member.id, new_password)
    # Revoke every other API token for this member - a stolen token
    # shouldn't survive an owner-initiated password change, same
    # reasoning as the website's own password-reset flow. The token
    # making *this* request is deliberately spared, so the device that
    # just changed the password doesn't get logged out by its own action.
    delete_other_api_tokens(member.id, token)
    json_response('200 OK', {'ok': True})


def main():
    member = current_api_member()
    if member is None:
        json_response('401 Unauthorized', {'error': 'Ogiltig eller saknad token.'})
        return

    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        json_response('200 OK', member_json(member))
        return

    values = read_json_body()
    action = values.get('action')

    if action == 'update_profile':
        handle_update_profile(member, values)
    elif action == 'change_password':
        handle_change_password(member, get_bearer_token(), values)
    else:
        json_response('400 Bad Request', {'error': 'Okänd åtgärd.'})


if __name__ == '__main__':
    main()
