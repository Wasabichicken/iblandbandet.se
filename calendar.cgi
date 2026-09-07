#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ical
from dal.events import list_all_events_utc


def main():
    host = os.environ.get('HTTP_HOST', 'iblandbandet.se')
    body = ical.build_calendar(list_all_events_utc(), host)
    print('Content-Type: text/calendar; charset=utf-8')
    print()
    print(body, end='')


if __name__ == '__main__':
    main()
