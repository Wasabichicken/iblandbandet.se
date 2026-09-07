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
    """Build a full https:// URL for an app-relative path, using the request's Host."""
    host = os.environ.get('HTTP_HOST', 'iblandbandet.se')
    return 'https://{}{}'.format(host, url(path))
