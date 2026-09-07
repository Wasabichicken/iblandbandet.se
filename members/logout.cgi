#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from dal.sessions import delete_session
from session_auth import get_session_token


def main():
    token = get_session_token()
    if token is not None:
        delete_session(token)

    is_https = os.environ.get('HTTPS') == 'on'
    secure = ' Secure;' if is_https else ''
    # Must mirror login.cgi's Secure/SameSite choice - an expiring
    # Set-Cookie only clears the matching cookie (same name/Path/Secure/
    # SameSite), not just anything with the same name.
    same_site = 'None' if is_https else 'Lax'

    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print('Set-Cookie: session=; Path=/; HttpOnly;{} SameSite={}; Max-Age=0'.format(secure, same_site))
    print()


if __name__ == '__main__':
    main()
