#!/usr/bin/env python3

import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from avatars import avatar_content_type, resolve_avatar_file
from session_auth import current_member


def forbidden():
    print('Status: 403 Forbidden')
    print('Content-Type: text/plain; charset=utf-8')
    print()


def not_found():
    print('Status: 404 Not Found')
    print('Content-Type: text/plain; charset=utf-8')
    print()


def main():
    member, _ = current_member()
    if member is None:
        # Hit as an <img src>, not a page navigation - a redirect here
        # would just render as a broken image, same as a plain 403 does,
        # so there's no reason to pretend this is a page.
        forbidden()
        return

    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    filename = query.get('file', [''])[0]

    full_path = resolve_avatar_file(filename)
    if full_path is None or not os.path.isfile(full_path):
        not_found()
        return

    content_type = avatar_content_type(filename)
    if content_type is None:
        forbidden()
        return

    with open(full_path, 'rb') as f:
        data = f.read()
    sys.stdout.write('Content-Type: {}\r\n'.format(content_type))
    sys.stdout.write('Content-Length: {}\r\n'.format(len(data)))
    sys.stdout.write('\r\n')
    sys.stdout.flush()
    sys.stdout.buffer.write(data)


if __name__ == '__main__':
    main()
