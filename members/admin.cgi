#!/usr/bin/env python3

import hmac
import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from dal.members import (DuplicateEmailError, admin_update_member, delete_member, get_member_by_id,
                          list_all_members)
from dal.subtitles import (create_subtitle, delete_subtitle, get_subtitle_by_id, list_all_subtitles,
                            update_subtitle)
from layout import render
from session_auth import current_member

REQUIRED_FIELD_LABELS = (
    ('email', 'E-post'),
)


def redirect_to_home():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print()


def swedish_list(items):
    if len(items) <= 1:
        return ''.join(items)
    return '{} och {}'.format(', '.join(items[:-1]), items[-1])


def missing_required_fields(values):
    return [label for field, label in REQUIRED_FIELD_LABELS if not values[field]]


def parse_id(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    values = {key: parsed.get(key, [''])[0].strip() for key in
              ('action', 'csrf_token', 'member_id', 'email', 'instruments',
               'description', 'name', 'subtitle_id', 'subtitle')}
    values['is_active'] = 'is_active' in parsed
    values['is_admin'] = 'is_admin' in parsed
    return values


def render_page(member, csrf_token, message=None, message_kind=None,
                 edit_member=None, edit_values=None, confirm_delete_member=None,
                 edit_subtitle=None, edit_subtitle_value=None, confirm_delete_subtitle=None):
    render(
        'admin.mako',
        title='Adminpanel — (i)Blandbandet',
        member=member,
        csrf_token=csrf_token,
        members=list_all_members(),
        subtitles=list_all_subtitles(),
        message=message,
        message_kind=message_kind,
        edit_member=edit_member,
        edit_values=edit_values,
        confirm_delete_member=confirm_delete_member,
        edit_subtitle=edit_subtitle,
        edit_subtitle_value=edit_subtitle_value,
        confirm_delete_subtitle=confirm_delete_subtitle,
    )


def handle_update_member(values):
    missing = missing_required_fields(values)
    if missing:
        return '{} måste fyllas i.'.format(swedish_list(missing)), 'error'

    try:
        admin_update_member(
            member_id=parse_id(values['member_id']),
            email=values['email'],
            instruments=values['instruments'] or None,
            description=values['description'] or None,
            is_active=values['is_active'],
            is_admin=values['is_admin'],
            name=values['name'] or None,
        )
    except DuplicateEmailError:
        return 'Det finns redan en medlem med den e-postadressen.', 'error'

    return '{} har uppdaterats.'.format(values['email']), 'success'


def handle_delete_member(member, target_id):
    if target_id == member.id:
        return 'Du kan inte ta bort ditt eget konto härifrån.', 'error'

    target = get_member_by_id(target_id)
    if target is None:
        return 'Medlemmen hittades inte.', 'error'

    delete_member(target_id)
    return '{} har tagits bort.'.format(target.email), 'success'


def handle_create_subtitle(text):
    if not text:
        return 'Rubriken får inte vara tom.', 'error'
    create_subtitle(text)
    return 'Rubriken har lagts till.', 'success'


def handle_update_subtitle(subtitle_id, text):
    if not text:
        return 'Rubriken får inte vara tom.', 'error'
    if get_subtitle_by_id(subtitle_id) is None:
        return 'Rubriken hittades inte.', 'error'
    update_subtitle(subtitle_id, text)
    return 'Rubriken har uppdaterats.', 'success'


def handle_delete_subtitle(target_id):
    target = get_subtitle_by_id(target_id)
    if target is None:
        return 'Rubriken hittades inte.', 'error'
    delete_subtitle(target_id)
    return 'Rubriken har tagits bort.', 'success'


def main():
    member, csrf_token = current_member()
    if member is None or not member.is_admin:
        redirect_to_home()
        return

    if os.environ.get('REQUEST_METHOD', 'GET') == 'POST':
        values = read_form()

        if not hmac.compare_digest(values['csrf_token'], csrf_token):
            render_page(member, csrf_token, message='Sessionen är ogiltig, ladda om sidan.', message_kind='error')
            return

        if values['action'] == 'update_member':
            message, kind = handle_update_member(values)
            if kind == 'error':
                target_id = parse_id(values['member_id'])
                target = get_member_by_id(target_id) if target_id is not None else None
                edit_values = {
                    'email': values['email'],
                    'instruments': values['instruments'],
                    'description': values['description'],
                    'is_active': values['is_active'],
                    'is_admin': values['is_admin'],
                    'name': values['name'],
                }
                render_page(member, csrf_token, message=message, message_kind=kind,
                            edit_member=target, edit_values=edit_values)
                return
            render_page(member, csrf_token, message=message, message_kind=kind)
            return

        if values['action'] == 'delete_member':
            target_id = parse_id(values['member_id'])
            if target_id is None:
                render_page(member, csrf_token, message='Medlemmen hittades inte.', message_kind='error')
                return
            message, kind = handle_delete_member(member, target_id)
            render_page(member, csrf_token, message=message, message_kind=kind)
            return

        if values['action'] == 'create_subtitle':
            message, kind = handle_create_subtitle(values['subtitle'])
            render_page(member, csrf_token, message=message, message_kind=kind)
            return

        if values['action'] == 'update_subtitle':
            subtitle_id = parse_id(values['subtitle_id'])
            target = get_subtitle_by_id(subtitle_id) if subtitle_id is not None else None
            if target is None:
                render_page(member, csrf_token, message='Rubriken hittades inte.', message_kind='error')
                return
            message, kind = handle_update_subtitle(subtitle_id, values['subtitle'])
            if kind == 'error':
                render_page(member, csrf_token, message=message, message_kind=kind,
                            edit_subtitle=target, edit_subtitle_value=values['subtitle'])
                return
            render_page(member, csrf_token, message=message, message_kind=kind)
            return

        if values['action'] == 'delete_subtitle':
            target_id = parse_id(values['subtitle_id'])
            if target_id is None:
                render_page(member, csrf_token, message='Rubriken hittades inte.', message_kind='error')
                return
            message, kind = handle_delete_subtitle(target_id)
            render_page(member, csrf_token, message=message, message_kind=kind)
            return

        render_page(member, csrf_token)
        return

    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    edit_id = parse_id(query.get('edit', [''])[0])
    confirm_delete_id = parse_id(query.get('confirm_delete', [''])[0])
    edit_subtitle_id = parse_id(query.get('edit_subtitle', [''])[0])
    confirm_delete_subtitle_id = parse_id(query.get('confirm_delete_subtitle', [''])[0])

    if edit_id is not None:
        target = get_member_by_id(edit_id)
        if target is None:
            render_page(member, csrf_token, message='Medlemmen hittades inte.', message_kind='error')
            return
        edit_values = {
            'email': target.email,
            'instruments': target.instruments or '',
            'description': target.description or '',
            'is_active': target.is_active,
            'is_admin': target.is_admin,
            'name': target.name or '',
        }
        render_page(member, csrf_token, edit_member=target, edit_values=edit_values)
        return

    if confirm_delete_id is not None:
        target = get_member_by_id(confirm_delete_id)
        if target is None:
            render_page(member, csrf_token, message='Medlemmen hittades inte.', message_kind='error')
            return
        render_page(member, csrf_token, confirm_delete_member=target)
        return

    if edit_subtitle_id is not None:
        target = get_subtitle_by_id(edit_subtitle_id)
        if target is None:
            render_page(member, csrf_token, message='Rubriken hittades inte.', message_kind='error')
            return
        render_page(member, csrf_token, edit_subtitle=target, edit_subtitle_value=target.subtitle)
        return

    if confirm_delete_subtitle_id is not None:
        target = get_subtitle_by_id(confirm_delete_subtitle_id)
        if target is None:
            render_page(member, csrf_token, message='Rubriken hittades inte.', message_kind='error')
            return
        render_page(member, csrf_token, confirm_delete_subtitle=target)
        return

    render_page(member, csrf_token)


if __name__ == '__main__':
    main()
