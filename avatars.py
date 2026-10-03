import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'avatars')
UPLOAD_URL_PREFIX = '/static/uploads/avatars/'

DICEBEAR_URL = 'https://api.dicebear.com/9.x/initials/svg?chars=1&seed={}'
DICEBEAR_TIMEOUT_SECONDS = 5


def fetch_initials_avatar(seed):
    """Fetch a single-letter DiceBear "initials" SVG for the given seed.

    `chars=1` forces DiceBear to always display just the seed's first letter
    (it otherwise shows up to 2, split on word boundaries) - the background
    color is still hashed from the *whole* seed, though, so passing a full
    email rather than just its first letter gives every member a distinct
    color even when they share a first letter, without changing what's shown.

    Returns the raw SVG bytes, or None if DiceBear can't be reached in time -
    callers should treat that as "no avatar generated this time", not a hard
    failure. Registration (and the backfill script) must still succeed even
    if DiceBear is briefly unreachable; the member just keeps the generic
    _default.svg fallback until the next opportunity to generate one.
    """
    url = DICEBEAR_URL.format(urllib.parse.quote(seed))
    try:
        with urllib.request.urlopen(url, timeout=DICEBEAR_TIMEOUT_SECONDS) as response:
            return response.read()
    except (urllib.error.URLError, OSError):
        return None


def generate_and_save_initials_avatar(member_id, email):
    """Generate a DiceBear initials avatar for a member - the displayed
    letter is their email's first character, but the seed sent to DiceBear
    is that letter plus a one-way hash of the *whole* email, not the email
    itself (a member's real address has no business leaving this server just
    to pick a background color). Members sharing a first letter still get
    different colors, since the hash still varies the color hash-derived
    from the seed; `chars=1` (see fetch_initials_avatar) keeps only the real
    first letter on display regardless of what follows it in the seed.
    Saved exactly like an uploaded photo would be (same directory, same
    filename convention, same permission-fixing).

    Returns the profile_picture URL to store, or None if DiceBear couldn't
    be reached - callers should leave profile_picture untouched in that
    case (the member keeps the generic _default.svg fallback).
    """
    letter = email[0].upper()
    email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()
    data = fetch_initials_avatar(letter + email_hash)
    if data is None:
        return None
    filename = '{}_initials.svg'.format(member_id)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, 'wb') as out:
        out.write(data)
    fix_upload_permissions(UPLOAD_DIR, file_path)
    return UPLOAD_URL_PREFIX + filename


_CONTENT_TYPES = {'.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}


def resolve_avatar_file(filename):
    """Validates a requested avatar filename stays within UPLOAD_DIR - same
    realpath-containment check scores_common.py's resolve_path() uses,
    since this comes from a query string parameter a logged-in member/API
    client controls directly. Returns the full path, or None if missing/
    outside UPLOAD_DIR."""
    if not filename:
        return None
    root = os.path.realpath(UPLOAD_DIR)
    target = os.path.realpath(os.path.join(root, filename))
    if target != root and not target.startswith(root + os.sep):
        return None
    return target


def avatar_content_type(filename):
    return _CONTENT_TYPES.get(os.path.splitext(filename)[1].lower())


def avatar_url(profile_picture):
    """The <img src> to use on the *website* for a member's avatar. The
    generic default stays a plain public static file (nothing about it
    identifies anyone); a real uploaded/generated avatar is only ever
    served through the login-gated members/avatar.cgi, never the raw
    static path it's actually stored under (see UPLOAD_URL_PREFIX)."""
    if not profile_picture:
        return '/static/img/avatars/_default.svg'
    filename = profile_picture[len(UPLOAD_URL_PREFIX):]
    return '/members/avatar.cgi?file=' + urllib.parse.quote(filename)


def api_avatar_url(profile_picture):
    """Same as avatar_url(), but for API responses - gated by the bearer-
    token-authenticated api/avatar.cgi instead of the website's session-
    cookie-gated members/avatar.cgi. Never base_path-prefixed: the API is
    only ever reached through the public proxied domain, same reasoning
    as every other URL api/*.cgi already hands back."""
    if not profile_picture:
        return '/static/img/avatars/_default.svg'
    filename = profile_picture[len(UPLOAD_URL_PREFIX):]
    return '/api/avatar.cgi?file=' + urllib.parse.quote(filename)


def fix_upload_permissions(directory, file_path):
    """Make an uploads directory/file readable by Apache's static-file server.

    On accum.se, CGI scripts run via suexec as the account's own user, so a
    file this process creates gets that user's restrictive default umask
    (confirmed empirically: 700/600) - fine for the CGI script itself, but
    Apache's plain static-file server runs as a different, unprivileged
    user and can't read it at all. `os.makedirs(..., exist_ok=True)` can
    silently create the parent directory too, so both need fixing, not
    just the immediate one - matches what a checked-in, rsync-deployed
    static file already has (775/664).
    """
    try:
        os.chmod(os.path.dirname(directory), 0o755)
    except OSError:
        pass
    try:
        os.chmod(directory, 0o755)
    except OSError:
        pass
    try:
        os.chmod(file_path, 0o644)
    except OSError:
        pass
