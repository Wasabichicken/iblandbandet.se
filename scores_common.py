import os

ALLOWED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.mp3': 'audio/mpeg',
    '.mscz': 'application/octet-stream',
    '.txt': 'text/plain; charset=utf-8',
}

# .mscz is a MuseScore project file (a zip archive) - no browser can render
# it inline, so it gets a real download instead of the browser trying (and
# failing) to display it the way it does for the other types.
DOWNLOAD_EXTENSIONS = {'.mscz'}


def fs_display_name(name):
    """Recover a real Unicode name from a filesystem name PEP-383-mangled
    by a non-UTF-8 locale.

    accum.se's CGI execution context doesn't have a UTF-8 locale (same
    root cause as the stdout-encoding bug in layout.py, just hitting a
    different mechanism) - os.listdir() can't decode multi-byte UTF-8
    filename bytes there, so Python falls back to one surrogate escape
    per raw byte instead of raising immediately. Those escapes still hold
    the exact original bytes, so re-encoding with the same handler and
    decoding as UTF-8 recovers the real name - but only for *display*:
    everything that touches the filesystem or builds a URL must keep
    using the original (possibly still-mangled) name, since re-mangling a
    repaired name back to disk-correct bytes would need the filesystem
    encoding to be right, which is exactly what's broken here. This also
    means a display name is always safe to put straight into JSON, since
    it's guaranteed to be real, valid Unicode - the raw name is not.
    """
    try:
        return name.encode('utf-8', 'surrogateescape').decode('utf-8')
    except UnicodeError:
        return name


def resolve_path(scores_root, relative_path):
    root = os.path.realpath(scores_root)
    target = os.path.realpath(os.path.join(root, relative_path))
    if target != root and not target.startswith(root + os.sep):
        return None
    return target
