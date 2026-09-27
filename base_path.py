import os


def get_base_path():
    """URL path prefix this app is served under.

    Locally the vhost DocumentRoot points straight at the repo, so the app
    IS the site root and this is ''. On accum.se the app lives under
    /~ericj/iblandbandet - APP_BASE_PATH is set via SetEnv in .htaccess,
    the same pattern as DB_CONNECTION_STRING/SCORES_ROOT. Never has a
    trailing slash, so callers can always just concatenate a leading-slash
    path onto the result.
    """
    return os.environ.get('APP_BASE_PATH', '').rstrip('/')


def url(path):
    """Prefix an app-relative path (starting with '/') with the base path."""
    return get_base_path() + path


def absolute_url(path):
    """Build a full https:// URL for an app-relative path, using the request's Host.

    Prefers X-Forwarded-Host over Host: requests proxied through the
    Cloudflare Worker (see cloudflare-worker/worker.js) hit this app with
    Host: www.accum.se (the Worker's own fetch target), while
    X-Forwarded-Host carries the real visitor-facing hostname
    (www.iblandbandet.se). When X-Forwarded-Host is present, this app's own
    /~ericj/iblandbandet base path is purely an accum.se implementation
    detail - the Worker already strips it from every proxied page - so the
    canonical iblandbandet.se URL is path alone, not url(path). Local dev
    and direct accum.se access never set X-Forwarded-Host, so they still
    get url(path) prefixed with the real base path, same as before.
    """
    forwarded_host = os.environ.get('HTTP_X_FORWARDED_HOST')
    if forwarded_host:
        return 'https://{}{}'.format(forwarded_host, path)
    host = os.environ.get('HTTP_HOST', 'iblandbandet.se')
    return 'https://{}{}'.format(host, url(path))
