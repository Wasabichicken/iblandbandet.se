#!/usr/bin/env python3

import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from dal.members import get_member_by_email, verify_password
from dal.sessions import create_session

SESSION_MAX_AGE = 30 * 24 * 60 * 60


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    return {
        'email': parsed.get('email', [''])[0].strip(),
        'password': parsed.get('password', [''])[0],
    }


def redirect(location, token=None):
    print('Status: 302 Found')
    print('Location: {}'.format(url(location)))
    if token:
        is_https = os.environ.get('HTTPS') == 'on'
        secure = ' Secure;' if is_https else ''
        # SameSite=None (needed for the accum.se-origin cookie to work
        # inside iblandbandet.se's cross-site Loopia iframe) requires
        # Secure or browsers reject the cookie outright - fall back to Lax
        # on plain-HTTP local dev, where Secure isn't set either.
        same_site = 'None' if is_https else 'Lax'
        print('Set-Cookie: session={}; Path=/; HttpOnly;{} SameSite={}; Max-Age={}'.format(
            token, secure, same_site, SESSION_MAX_AGE))
    print()


def main():
    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        redirect('/')
        return

    values = read_form()

    if not values['email']:
        redirect('/?login_failed=1')
        return

    member = get_member_by_email(values['email'])
    if member is None:
        redirect('/?login_failed=1')
        return

    if not verify_password(values['password'], member.password_salt, member.password_hash,
                            member.password_iterations):
        redirect('/?login_failed=1')
        return

    token, _ = create_session(member.id)
    redirect('/', token=token)


if __name__ == '__main__':
    main()
