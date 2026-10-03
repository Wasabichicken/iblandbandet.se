#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_common import json_response, read_json_body
from avatars import api_avatar_url
from dal.api_tokens import create_api_token
from dal.members import get_member_by_email, verify_password


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


def main():
    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        json_response('405 Method Not Allowed', {'error': 'POST krävs.'})
        return

    values = read_json_body()
    email = values.get('email', '').strip()
    password = values.get('password', '')

    # Same generic failure regardless of which check fails - same
    # reasoning as members/login.cgi and forgot_password.cgi: never
    # reveal whether a given email is a registered member.
    member = get_member_by_email(email) if email else None
    if member is None or not verify_password(
            password, member.password_salt, member.password_hash, member.password_iterations):
        json_response('401 Unauthorized', {'error': 'Fel e-postadress eller lösenord.'})
        return

    token = create_api_token(member.id)
    json_response('200 OK', {'token': token, 'member': member_json(member)})


if __name__ == '__main__':
    main()
