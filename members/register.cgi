#!/usr/bin/env python3

import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from avatars import generate_and_save_initials_avatar
from dal.members import DuplicateEmailError, register_member, update_profile_picture
from layout import render
from session_auth import current_member

FIELDS = ('email', 'password', 'instruments')
REQUIRED_FIELD_LABELS = (
    ('email', 'E-post'),
    ('password', 'Lösenord'),
)


def missing_required_fields(values):
    return [label for field, label in REQUIRED_FIELD_LABELS if not values[field]]


def swedish_list(items):
    if len(items) <= 1:
        return ''.join(items)
    return '{} och {}'.format(', '.join(items[:-1]), items[-1])


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    values = {field: parsed.get(field, [''])[0].strip() for field in FIELDS}
    values['is_active'] = 'is_active' in parsed
    return values


def render_page(message=None, message_kind=None, values=None):
    member, _ = current_member()
    render(
        'register.mako',
        title='Registrera medlem — (i)Blandbandet',
        member=member,
        message=message,
        message_kind=message_kind,
        values=values or {},
    )


def main():
    method = os.environ.get('REQUEST_METHOD', 'GET')

    if method != 'POST':
        render_page(values={'is_active': True})
        return

    values = read_form()

    missing = missing_required_fields(values)
    if missing:
        render_page(
            message='{} måste fyllas i.'.format(swedish_list(missing)),
            message_kind='error',
            values=values,
        )
        return

    try:
        member_id = register_member(
            email=values['email'],
            password=values['password'],
            instruments=values['instruments'] or None,
            is_active=values['is_active'],
        )
    except DuplicateEmailError:
        render_page(
            message='Det finns redan en medlem med e-postadressen {}.'.format(values['email']),
            message_kind='error',
            values=values,
        )
        return

    # If DiceBear can't be reached, the member just keeps the generic
    # _default.svg fallback - registration itself must not fail because of it.
    picture_url = generate_and_save_initials_avatar(member_id, values['email'])
    if picture_url:
        update_profile_picture(member_id, picture_url)

    render_page(
        message='Registreringen har genomförts.',
        message_kind='success',
        values={'is_active': True},
    )


if __name__ == '__main__':
    main()
