import os


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
