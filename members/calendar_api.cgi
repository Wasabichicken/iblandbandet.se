#!/usr/bin/env python3

import hmac
import json
import os
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dal.events import create_event, delete_event, list_all_events, update_event
from session_auth import current_member


def json_response(status, payload):
    print('Status: {}'.format(status))
    print('Content-Type: application/json; charset=utf-8')
    print()
    print(json.dumps(payload))


def format_datetime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S') if dt else None


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    return {key: parsed.get(key, [''])[0].strip() for key in
            ('action', 'csrf_token', 'event_id', 'title', 'starts_at', 'ends_at',
             'location', 'latitude', 'longitude', 'description')}


def parse_coordinate(raw):
    try:
        return float(raw)
    except ValueError:
        return None


def handle_list():
    # Deliberately public (no login check) - same reasoning as the .ics feed:
    # nothing sensitive in a rehearsal schedule, and it powers the read-only
    # calendar on the homepage. Mutations (create/update/delete) stay gated.
    events = [
        {
            'id': event_id,
            'title': title,
            'start': format_datetime(starts_at),
            'end': format_datetime(ends_at),
            'extendedProps': {
                'location': location or '',
                'latitude': latitude,
                'longitude': longitude,
                'description': description or '',
            },
        }
        for event_id, title, starts_at, ends_at, location, latitude, longitude, description
        in list_all_events()
    ]
    json_response('200 OK', events)


def handle_create(member, values):
    if not values['title'] or not values['starts_at']:
        json_response('400 Bad Request', {'error': 'Titel och starttid måste fyllas i.'})
        return

    event_id = create_event(
        title=values['title'],
        starts_at=values['starts_at'],
        ends_at=values['ends_at'] or None,
        location=values['location'] or None,
        latitude=parse_coordinate(values['latitude']),
        longitude=parse_coordinate(values['longitude']),
        description=values['description'] or None,
        created_by=member.id,
    )
    json_response('200 OK', {'id': event_id})


def handle_update(values):
    if not values['event_id'].isdigit() or not values['title'] or not values['starts_at']:
        json_response('400 Bad Request', {'error': 'Ogiltiga uppgifter.'})
        return

    update_event(
        event_id=int(values['event_id']),
        title=values['title'],
        starts_at=values['starts_at'],
        ends_at=values['ends_at'] or None,
        location=values['location'] or None,
        latitude=parse_coordinate(values['latitude']),
        longitude=parse_coordinate(values['longitude']),
        description=values['description'] or None,
    )
    json_response('200 OK', {'ok': True})


def handle_delete(values):
    if not values['event_id'].isdigit():
        json_response('400 Bad Request', {'error': 'Ogiltigt id.'})
        return

    delete_event(int(values['event_id']))
    json_response('200 OK', {'ok': True})


def main():
    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        handle_list()
        return

    member, csrf_token = current_member()
    if member is None:
        json_response('403 Forbidden', {'error': 'Inte inloggad.'})
        return

    values = read_form()

    if not hmac.compare_digest(values['csrf_token'], csrf_token):
        json_response('403 Forbidden', {'error': 'Sessionen är ogiltig, ladda om sidan.'})
        return

    if values['action'] == 'create':
        handle_create(member, values)
    elif values['action'] == 'update':
        handle_update(values)
    elif values['action'] == 'delete':
        handle_delete(values)
    else:
        json_response('400 Bad Request', {'error': 'Okänd åtgärd.'})


if __name__ == '__main__':
    main()
