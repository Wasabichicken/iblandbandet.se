#!/usr/bin/env python3

import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from dal.members import update_password
from dal.password_resets import consume_reset, get_reset
from dal.sessions import delete_sessions_for_member
from layout import render
from session_auth import current_member

INVALID_TOKEN_MESSAGE = 'Länken är ogiltig eller har gått ut. Begär en ny länk för att byta lösenord.'


def render_invalid(member):
    render('reset_password.mako', title='Byt lösenord — (i)Blandbandet', member=member,
           token=None, message=INVALID_TOKEN_MESSAGE, message_kind='error')


def render_form(member, token, message=None, message_kind=None):
    render('reset_password.mako', title='Byt lösenord — (i)Blandbandet', member=member,
           token=token, message=message, message_kind=message_kind)


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    return {
        'token': parsed.get('token', [''])[0].strip(),
        'new_password': parsed.get('new_password', [''])[0],
        'confirm_password': parsed.get('confirm_password', [''])[0],
    }


def redirect_to_home_reset():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/?password_reset=1')))
    print()


def main():
    member, _ = current_member()

    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        query = parse_qs(os.environ.get('QUERY_STRING', ''))
        token = query.get('token', [''])[0].strip()
        if not token or get_reset(token) is None:
            render_invalid(member)
            return
        render_form(member, token)
        return

    values = read_form()
    reset = get_reset(values['token'])
    if reset is None:
        render_invalid(member)
        return

    if not values['new_password']:
        render_form(member, values['token'], message='Nytt lösenord måste fyllas i.', message_kind='error')
        return

    if values['new_password'] != values['confirm_password']:
        render_form(member, values['token'], message='Lösenorden stämmer inte överens.', message_kind='error')
        return

    update_password(reset.member_id, values['new_password'])
    consume_reset(values['token'])
    delete_sessions_for_member(reset.member_id)
    redirect_to_home_reset()


if __name__ == '__main__':
    main()
