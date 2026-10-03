from dal.db import get_connection

# created_at is always selected via AT TIME ZONE 'UTC' - unlike events/drive,
# chat has exactly one consumer (the API - see CHAT.md, never rendered on
# the website), so there's no naive-local-time website reader to stay
# compatible with. Every row this module returns is genuine UTC, full stop,
# same reasoning as list_all_events_utc() but without needing a separate
# naive-local variant alongside it, since nothing here ever needs one.


def create_message(member_id, body=None, image_uuid=None, image_size_bytes=None, request_id=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_chat_messages (member_id, body, image_uuid, image_size_bytes, request_id)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, created_at AT TIME ZONE 'UTC' AS created_at
            """,
            member_id, body, image_uuid, image_size_bytes, request_id,
        )
        row = cursor.fetchone()
        return row.id, row.created_at
    finally:
        connection.close()


def get_message_by_id(message_id):
    # Includes the same profile_picture/name LEFT JOIN as list_messages() -
    # needed so that re-fetching a message after an edit (see
    # api/chat.cgi's handle_edit()) reflects the *original sender's* info
    # even when an admin is the one editing someone else's message, not the
    # editing admin's own.
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes, c.request_id,
                   c.created_at AT TIME ZONE 'UTC' AS created_at,
                   c.edited_at AT TIME ZONE 'UTC' AS edited_at, m.profile_picture, m.name
            FROM iblandbandet_chat_messages c
            LEFT JOIN iblandbandet_members m ON m.id = c.member_id
            WHERE c.id = ?
            """,
            message_id,
        )
        return cursor.fetchone()
    finally:
        connection.close()


def get_message_by_request_id(request_id):
    # Used to detect a retried send before attempting the INSERT - a client
    # that resent the same request_id after a dropped connection/timeout
    # gets back the message that was already saved, instead of hitting the
    # UNIQUE constraint as a raw database error. Includes the same
    # profile_picture/name LEFT JOIN as list_messages()/get_message_by_id() -
    # this row gets handed straight to message_json(), which expects those
    # columns to be there.
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes, c.request_id,
                   c.created_at AT TIME ZONE 'UTC' AS created_at,
                       c.edited_at AT TIME ZONE 'UTC' AS edited_at, m.profile_picture, m.name
            FROM iblandbandet_chat_messages c
            LEFT JOIN iblandbandet_members m ON m.id = c.member_id
            WHERE c.request_id = ?
            """,
            request_id,
        )
        return cursor.fetchone()
    finally:
        connection.close()


def list_messages(before_id=None, limit=50):
    # Newest-first, like any chat history - the caller reverses for display
    # if it wants chronological order. `before_id` pages backward through
    # older history; omitted, this returns the most recent `limit` messages.
    #
    # LEFT JOINs the sender's profile_picture and name (their optional,
    # self-chosen "Artistnamn" - see schema.sql) - same pattern dal/drive.py
    # already uses for an item's owner, rather than making the API expose a
    # general "look up any member by id" endpoint just to resolve either.
    # LEFT (not inner) JOIN so a message from a since-deleted member
    # (member_id is NULL - see the table's ON DELETE SET NULL) still comes
    # back with both simply NULL, not dropped from history.
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if before_id is None:
            cursor.execute(
                """
                SELECT c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes, c.request_id,
                       c.created_at AT TIME ZONE 'UTC' AS created_at,
                       c.edited_at AT TIME ZONE 'UTC' AS edited_at, m.profile_picture, m.name
                FROM iblandbandet_chat_messages c
                LEFT JOIN iblandbandet_members m ON m.id = c.member_id
                ORDER BY c.id DESC
                LIMIT ?
                """,
                limit,
            )
        else:
            cursor.execute(
                """
                SELECT c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes, c.request_id,
                       c.created_at AT TIME ZONE 'UTC' AS created_at,
                       c.edited_at AT TIME ZONE 'UTC' AS edited_at, m.profile_picture, m.name
                FROM iblandbandet_chat_messages c
                LEFT JOIN iblandbandet_members m ON m.id = c.member_id
                WHERE c.id < ?
                ORDER BY c.id DESC
                LIMIT ?
                """,
                before_id, limit,
            )
        return cursor.fetchall()
    finally:
        connection.close()


def update_message_body(message_id, body):
    # Overwrites in place - no edit history kept, same trusting, no-audit-
    # trail posture as everything else here. edited_at marks that *an* edit
    # happened and when the latest one was; it doesn't accumulate a log.
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE iblandbandet_chat_messages SET body = ?, edited_at = now() WHERE id = ?",
            body, message_id,
        )
    finally:
        connection.close()


def delete_message(message_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_chat_messages WHERE id = ?", message_id)
    finally:
        connection.close()
