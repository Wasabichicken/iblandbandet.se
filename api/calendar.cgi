#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_auth import current_api_member
from api_common import json_response, read_json_body
from dal.events import create_event, delete_event, list_all_events_utc, update_event


def format_datetime(dt):
    # list_all_events_utc() already converts to naive UTC wall-clock values
    # in SQL (see dal/events.py) - appending Z here is just spelling that
    # out as real ISO-8601, unlike the website widget's own JSON endpoint,
    # which hands FullCalendar naive local-Stockholm-time strings with no
    # offset at all. That's fine for a browser in the same timezone as the
    # events were entered in; it's not something a generic API client
    # should have to assume.
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None


def event_json(row):
    (event_id, title, starts_at, ends_at, location, latitude, longitude, description) = row
    return {
        'id': event_id,
        'title': title,
        'starts_at': format_datetime(starts_at),
        'ends_at': format_datetime(ends_at),
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'description': description,
    }


def handle_list():
    # Deliberately public, same reasoning as the .ics feed and the
    # website's own calendar_api.cgi: nothing sensitive in a rehearsal
    # schedule.
    json_response('200 OK', [event_json(row) for row in list_all_events_utc()])


def handle_create(member, values):
    title = (values.get('title') or '').strip()
    starts_at = (values.get('starts_at') or '').strip()
    if not title or not starts_at:
        json_response('400 Bad Request', {'error': 'title och starts_at måste fyllas i.'})
        return

    event_id = create_event(
        title=title,
        starts_at=starts_at,
        ends_at=(values.get('ends_at') or None),
        location=(values.get('location') or None),
        latitude=values.get('latitude'),
        longitude=values.get('longitude'),
        description=(values.get('description') or None),
        created_by=member.id,
    )
    json_response('200 OK', {'id': event_id})


def handle_update(values):
    event_id = values.get('event_id')
    title = (values.get('title') or '').strip()
    starts_at = (values.get('starts_at') or '').strip()
    if not isinstance(event_id, int) or not title or not starts_at:
        json_response('400 Bad Request', {'error': 'Ogiltiga uppgifter.'})
        return

    update_event(
        event_id=event_id,
        title=title,
        starts_at=starts_at,
        ends_at=(values.get('ends_at') or None),
        location=(values.get('location') or None),
        latitude=values.get('latitude'),
        longitude=values.get('longitude'),
        description=(values.get('description') or None),
    )
    json_response('200 OK', {'ok': True})


def handle_delete(values):
    event_id = values.get('event_id')
    if not isinstance(event_id, int):
        json_response('400 Bad Request', {'error': 'Ogiltigt id.'})
        return

    delete_event(event_id)
    json_response('200 OK', {'ok': True})


def main():
    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        handle_list()
        return

    member = current_api_member()
    if member is None:
        json_response('401 Unauthorized', {'error': 'Ogiltig eller saknad token.'})
        return

    values = read_json_body()
    action = values.get('action')

    if action == 'create':
        handle_create(member, values)
    elif action == 'update':
        handle_update(values)
    elif action == 'delete':
        handle_delete(values)
    else:
        json_response('400 Bad Request', {'error': 'Okänd åtgärd.'})


if __name__ == '__main__':
    main()
