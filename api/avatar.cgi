#!/usr/bin/env python3

import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_auth import current_api_member
from api_common import json_response
from avatars import avatar_content_type, resolve_avatar_file


def main():
    member = current_api_member()
    if member is None:
        json_response('401 Unauthorized', {'error': 'Ogiltig eller saknad token.'})
        return

    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    filename = query.get('file', [''])[0]

    full_path = resolve_avatar_file(filename)
    if full_path is None or not os.path.isfile(full_path):
        json_response('404 Not Found', {'error': 'Bilden hittades inte.'})
        return

    content_type = avatar_content_type(filename)
    if content_type is None:
        json_response('400 Bad Request', {'error': 'Okänd bildtyp.'})
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
