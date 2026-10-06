#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from dal.api_tokens import create_api_token
from layout import render
from session_auth import current_member


def redirect_to_home():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print()


def main():
    member, _ = current_member()
    if member is None:
        redirect_to_home()
        return

    # A fresh API token minted for this page load - the website's session
    # cookie and the API's bearer tokens are deliberately separate
    # mechanisms (see CHAT.md), so the page's own JS needs a real token of
    # its own to talk to api/chat.cgi and the chat relay, the exact same
    # way the mobile app does. Not revoked on page unload (a known, minor,
    # accepted loose end - see CHAT.md) - tokens don't expire on their own
    # either, same as every other API token.
    chat_token = create_api_token(member.id)

    render(
        'chat.mako',
        title='Chatt — (i)Blandbandet',
        member=member,
        chat_token=chat_token,
        chat_ws_url=os.environ.get('CHAT_WS_URL', ''),
    )


if __name__ == '__main__':
    main()
