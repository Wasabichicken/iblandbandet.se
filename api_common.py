import json
import os
import sys


def json_response(status, payload):
    print('Status: {}'.format(status))
    print('Content-Type: application/json; charset=utf-8')
    print()
    print(json.dumps(payload))


def read_json_body():
    """Parse the request body as JSON, returning {} on any malformed input -
    callers treat a missing required field the same way whether the body
    was absent, not JSON, or just missing that key.
    """
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    try:
        parsed = json.loads(body)
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
