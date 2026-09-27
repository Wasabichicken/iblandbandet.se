#!/usr/bin/env python3

import datetime
import os
import sys
from urllib.parse import parse_qs, quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import url
from layout import render
from scores_common import ALLOWED_EXTENSIONS, DOWNLOAD_EXTENSIONS, fs_display_name, resolve_path
from session_auth import current_member

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
    # print() buffers through sys.stdout's own text layer, while render()
    # writes bytes straight to sys.stdout.buffer beneath it - without an
    # explicit flush here, the two can reach the underlying stream out of
    # order, so this "Status:" line arrives after render()'s output instead
    # of before it, and the CGI response ends up 200 OK instead of `status`.
    print('Status: {}'.format(status))
    sys.stdout.flush()
    render('error.mako', title='{} — (i)Blandbandet'.format(message), member=member, message=message)


def get_requested_path():
    query = parse_qs(os.environ.get('QUERY_STRING', ''))
    return query.get('path', [''])[0].lstrip('/')


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
            title='Noter — (i)Blandbandet',
            member=member,
            relative_path=relative_path,
            breadcrumb=build_breadcrumb(relative_path),
            entries=list_directory(full_path),
        )
    else:
        serve_file(member, full_path, os.path.basename(full_path))


if __name__ == '__main__':
    main()
