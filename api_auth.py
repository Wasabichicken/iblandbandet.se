import os

from dal.api_tokens import get_api_token_member_id
from dal.members import get_member_by_id

BEARER_PREFIX = 'Bearer '


def get_bearer_token():
    # Apache does not pass the Authorization header into the CGI
    # environment by default - .htaccess needs `CGIPassAuth On` (Apache
    # 2.4.13+) for HTTP_AUTHORIZATION to ever be set at all. Confirmed
    # empirically on accum.se before relying on this.
    header = os.environ.get('HTTP_AUTHORIZATION', '')
    if not header.startswith(BEARER_PREFIX):
        return None
    return header[len(BEARER_PREFIX):].strip() or None


def current_api_member():
    """Return the member row for the request's bearer token, or None."""
    token = get_bearer_token()
    if token is None:
        return None
    member_id = get_api_token_member_id(token)
    if member_id is None:
        return None
    return get_member_by_id(member_id)
