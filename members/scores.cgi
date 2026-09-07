#!/usr/bin/env python3

import datetime
import os
import sys
from urllib.parse import parse_qs, quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from layout import render
from session_auth import current_member

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

SWEDISH_MONTHS = (
    'jan', 'feb', 'mar', 'apr', 'maj', 'jun',
    'jul', 'aug', 'sep', 'okt', 'nov', 'dec',
)


def format_date(timestamp):
    d = datetime.date.fromtimestamp(timestamp)
    return '{} {} {}'.format(d.day, SWEDISH_MONTHS[d.month - 1], d.year)


def format_size(num_bytes):
    if num_bytes < 1000:
        return '{} B'.format(num_bytes)
    for unit in ('kB', 'MB', 'GB'):
        num_bytes /= 1000.0
        if num_bytes < 1000 or unit == 'GB':
            return '{} {}'.format(str(round(num_bytes, 1)).replace('.', ','), unit)


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
    encoding to be right, which is exactly what's broken here.
    """
    try:
        return name.encode('utf-8', 'surrogateescape').decode('utf-8')
    except UnicodeError:
        return name


def build_breadcrumb(relative_path):
    segments = [s for s in relative_path.split('/') if s]
    crumbs = []
    for i, segment in enumerate(segments, start=1):
        crumbs.append({
            'display_name': fs_display_name(segment),
            # errors='surrogateescape': segments may still carry raw,
            # un-decodable filename bytes (see fs_display_name) - this
            # quotes the true original bytes instead of crashing on them.
            'href_path': quote('/'.join(segments[:i]), errors='surrogateescape'),
            'is_current': i == len(segments),
        })
    return crumbs


def redirect_to_home():
    print('Status: 302 Found')
    print('Location: {}'.format(url('/')))
    print()


def error_page(member, status, message):
    print('Status: {}'.format(status))
    render('error.mako', title='{} — iBlandbandet'.format(message), member=member, message=message)


def get_requested_path():
    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    return query.get('path', [''])[0].lstrip('/')


def resolve_path(scores_root, relative_path):
    root = os.path.realpath(scores_root)
    target = os.path.realpath(os.path.join(root, relative_path))
    if target != root and not target.startswith(root + os.sep):
        return None
    return target


def describe_entry(entry_path, name, is_dir):
    stat = os.stat(entry_path)
    return {
        'name': name,
        'display_name': fs_display_name(name),
        'is_dir': is_dir,
        'ext': None if is_dir else os.path.splitext(name)[1].lower(),
        'modified': format_date(stat.st_mtime),
        'size': None if is_dir else format_size(stat.st_size),
    }


def list_directory(full_path):
    dirs, files = [], []
    for name in sorted(os.listdir(full_path), key=str.lower):
        if name.startswith('.') or name.startswith('@'):
            continue
        entry_path = os.path.join(full_path, name)
        if os.path.isdir(entry_path):
            dirs.append(describe_entry(entry_path, name, is_dir=True))
        elif os.path.splitext(name)[1].lower() in ALLOWED_EXTENSIONS:
            files.append(describe_entry(entry_path, name, is_dir=False))
    return dirs + files


def serve_file(member, full_path, name):
    ext = os.path.splitext(name)[1].lower()
    content_type = ALLOWED_EXTENSIONS.get(ext)
    if content_type is None:
        error_page(member, '403 Forbidden', 'Den filtypen kan inte visas.')
        return

    display = fs_display_name(name)
    ascii_name = display.encode('ascii', 'replace').decode('ascii')
    disposition = 'attachment' if ext in DOWNLOAD_EXTENSIONS else 'inline'
    sys.stdout.write('Content-Type: {}\r\n'.format(content_type))
    sys.stdout.write('Content-Length: {}\r\n'.format(os.path.getsize(full_path)))
    sys.stdout.write('Content-Disposition: {}; filename="{}"; filename*=UTF-8\'\'{}\r\n'.format(
        disposition, ascii_name, quote(display)))
    sys.stdout.write('\r\n')
    sys.stdout.flush()
    with open(full_path, 'rb') as f:
        sys.stdout.buffer.write(f.read())


def main():
    member, _ = current_member()
    if member is None:
        redirect_to_home()
        return

    scores_root = os.environ.get('SCORES_ROOT')
    if not scores_root:
        error_page(member, '500 Internal Server Error', 'Notarkivet är inte konfigurerat.')
        return

    relative_path = get_requested_path()
    full_path = resolve_path(scores_root, relative_path)

    if full_path is None or not os.path.exists(full_path):
        error_page(member, '404 Not Found', 'Hittades inte.')
        return

    if os.path.isdir(full_path):
        render(
            'scores.mako',
            title='Noter — iBlandbandet',
            member=member,
            relative_path=relative_path,
            breadcrumb=build_breadcrumb(relative_path),
            entries=list_directory(full_path),
        )
    else:
        serve_file(member, full_path, os.path.basename(full_path))


if __name__ == '__main__':
    main()
