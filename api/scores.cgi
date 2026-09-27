#!/usr/bin/env python3

import datetime
import os
import sys
from urllib.parse import parse_qs, quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_auth import current_api_member
from api_common import json_response
from scores_common import ALLOWED_EXTENSIONS, DOWNLOAD_EXTENSIONS, fs_display_name, resolve_path


def get_requested_path():
    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    return query.get('path', [''])[0].lstrip('/')


def iso_utc(timestamp):
    # os.stat's mtime is always a real Unix timestamp (seconds since the
    # UTC epoch, unambiguous by definition) - no timezone-database lookup
    # or DST handling needed here, unlike the calendar's TIMESTAMPTZ
    # columns, which come back from Postgres in a specific session
    # timezone and need converting.
    return datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')


def build_breadcrumb(relative_path):
    segments = [s for s in relative_path.split('/') if s]
    crumbs = []
    for i, segment in enumerate(segments, start=1):
        crumbs.append({
            'name': fs_display_name(segment),
            'path': quote('/'.join(segments[:i]), errors='surrogateescape'),
        })
    return crumbs


def describe_entry(entry_path, name, relative_path, is_dir):
    stat = os.stat(entry_path)
    entry_relative = '/'.join(p for p in (relative_path, name) if p)
    return {
        # A raw filesystem name can carry bytes that aren't valid UTF-8
        # (see fs_display_name in scores_common.py) - JSON output must be
        # real Unicode, so "name" is always the recovered display name,
        # never the raw one. "path" is what the client sends back as
        # ?path=... to descend into or download this entry; quoting with
        # surrogateescape (matching the website's own breadcrumb links)
        # keeps it correct even for a name that didn't decode cleanly,
        # and the quoted, percent-encoded result is always plain ASCII,
        # so it's always safe to put in JSON regardless.
        'name': fs_display_name(name),
        'path': quote(entry_relative, errors='surrogateescape'),
        'is_dir': is_dir,
        'ext': None if is_dir else os.path.splitext(name)[1].lower(),
        'modified': iso_utc(stat.st_mtime),
        'size': None if is_dir else stat.st_size,
    }


def list_directory(full_path, relative_path):
    dirs, files = [], []
    for name in sorted(os.listdir(full_path), key=str.lower):
        if name.startswith('.') or name.startswith('@'):
            continue
        entry_path = os.path.join(full_path, name)
        if os.path.isdir(entry_path):
            dirs.append(describe_entry(entry_path, name, relative_path, is_dir=True))
        elif os.path.splitext(name)[1].lower() in ALLOWED_EXTENSIONS:
            files.append(describe_entry(entry_path, name, relative_path, is_dir=False))
    return dirs + files


def serve_file(full_path, name):
    ext = os.path.splitext(name)[1].lower()
    content_type = ALLOWED_EXTENSIONS.get(ext)
    if content_type is None:
        json_response('403 Forbidden', {'error': 'Den filtypen kan inte visas.'})
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
    member = current_api_member()
    if member is None:
        json_response('401 Unauthorized', {'error': 'Ogiltig eller saknad token.'})
        return

    scores_root = os.environ.get('SCORES_ROOT')
    if not scores_root:
        json_response('500 Internal Server Error', {'error': 'Notarkivet är inte konfigurerat.'})
        return

    relative_path = get_requested_path()
    full_path = resolve_path(scores_root, relative_path)

    if full_path is None or not os.path.exists(full_path):
        json_response('404 Not Found', {'error': 'Hittades inte.'})
        return

    if os.path.isdir(full_path):
        json_response('200 OK', {
            'path': quote(relative_path, errors='surrogateescape'),
            'breadcrumb': build_breadcrumb(relative_path),
            'entries': list_directory(full_path, relative_path),
        })
    else:
        serve_file(full_path, os.path.basename(full_path))


if __name__ == '__main__':
    main()
