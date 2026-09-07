import os
from http.cookies import SimpleCookie

from dal.members import get_member_by_id
from dal.sessions import get_session

COOKIE_NAME = 'session'


def get_session_token():
    cookie = SimpleCookie()
    cookie.load(os.environ.get('HTTP_COOKIE', ''))
    if COOKIE_NAME not in cookie:
        return None
    return cookie[COOKIE_NAME].value


def current_member():
    """Return (member_row, csrf_token) for the request's session cookie, or (None, None)."""
    token = get_session_token()
    if token is None:
        return None, None
    session = get_session(token)
    if session is None:
        return None, None
    return get_member_by_id(session.member_id), session.csrf_token
