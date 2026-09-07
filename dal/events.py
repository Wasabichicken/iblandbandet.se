from dal.db import get_connection


def list_upcoming_events():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, title, starts_at, ends_at, location, latitude, longitude, description
            FROM iblandbandet_events
            WHERE starts_at >= now() - interval '1 day'
            ORDER BY starts_at
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def list_all_events():
    # Naive datetimes here are in the ODBC session's timezone (Europe/Stockholm),
    # not UTC - correct for handing straight to FullCalendar, which treats a
    # timezone-less ISO string as floating/local to the viewer's browser. Since
    # our members are all in the same timezone the events were entered in, no
    # conversion is needed here (contrast with list_all_events_utc, used by the
    # ICS feed, which genuinely needs true UTC for portability).
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, title, starts_at, ends_at, location, latitude, longitude, description
            FROM iblandbandet_events
            ORDER BY starts_at
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def list_all_events_utc():
    # Timestamps come back already converted to naive UTC wall-clock values
    # (via AT TIME ZONE), so callers never need Python-side timezone math -
    # zoneinfo isn't available on remote Python 3.6.9, and a fixed UTC
    # offset would be wrong half the year (Sweden observes DST).
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, title, starts_at AT TIME ZONE 'UTC', ends_at AT TIME ZONE 'UTC',
                   location, latitude, longitude, description
            FROM iblandbandet_events
            ORDER BY starts_at
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def create_event(title, starts_at, ends_at, location, latitude, longitude, description, created_by):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_events (title, starts_at, ends_at, location, latitude, longitude,
                                 description, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            title, starts_at, ends_at, location, latitude, longitude, description, created_by,
        )
        cursor.execute("SELECT lastval()")
        return cursor.fetchone()[0]
    finally:
        connection.close()


def update_event(event_id, title, starts_at, ends_at, location, latitude, longitude, description):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE iblandbandet_events SET title = ?, starts_at = ?, ends_at = ?, location = ?,
                               latitude = ?, longitude = ?, description = ?
            WHERE id = ?
            """,
            title, starts_at, ends_at, location, latitude, longitude, description, event_id,
        )
    finally:
        connection.close()


def delete_event(event_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_events WHERE id = ?", event_id)
    finally:
        connection.close()
