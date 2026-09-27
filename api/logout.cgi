#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_auth import get_bearer_token
from api_common import json_response
from dal.api_tokens import delete_api_token


def main():
    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        json_response('405 Method Not Allowed', {'error': 'POST krävs.'})
        return

    token = get_bearer_token()
    if token is not None:
        delete_api_token(token)

    # Deleting a token that was never valid is still a successful logout
    # from the caller's point of view - nothing to report either way.
    json_response('200 OK', {'ok': True})


if __name__ == '__main__':
    main()
