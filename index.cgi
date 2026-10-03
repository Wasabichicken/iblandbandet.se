#!/usr/bin/env python3

import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_path import absolute_url, url
from dal.subtitles import get_random_subtitle
from layout import render
from session_auth import current_member

DEFAULT_SUBTITLE = 'Blandad musik, ibland'


def main():
    member, csrf_token = current_member()
    host = os.environ.get('HTTP_HOST', 'iblandbandet.se')
    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    render(
        'index.mako',
        title='(i)Blandbandet',
        member=member,
        csrf_token=csrf_token or '',
        feed_url=absolute_url('/calendar.ics'),
        webcal_url='webcal://{}{}'.format(host, url('/calendar.ics')),
        login_failed='login_failed' in query,
        password_reset='password_reset' in query,
        account_deleted='account_deleted' in query,
        subtitle=get_random_subtitle() or DEFAULT_SUBTITLE,
    )


if __name__ == '__main__':
    main()
