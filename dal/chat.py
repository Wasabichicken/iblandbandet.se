from dal.db import get_connection

# created_at is always selected via AT TIME ZONE 'UTC' - unlike events/drive,
# chat has exactly one consumer (the API - see CHAT.md, never rendered on
# the website), so there's no naive-local-time website reader to stay
# compatible with. Every row this module returns is genuine UTC, full stop,
# same reasoning as list_all_events_utc() but without needing a separate
# naive-local variant alongside it, since nothing here ever needs one.


def create_message(member_id, body=None, image_uuid=None, image_size_bytes=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_chat_messages (member_id, body, image_uuid, image_size_bytes)
            VALUES (?, ?, ?, ?)
            RETURNING id, created_at AT TIME ZONE 'UTC' AS created_at
            """,
            member_id, body, image_uuid, image_size_bytes,
        )
        row = cursor.fetchone()
        return row.id, row.created_at
    finally:
        connection.close()


def get_message_by_id(message_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, member_id, body, image_uuid, image_size_bytes,
                   created_at AT TIME ZONE 'UTC' AS created_at
            FROM iblandbandet_chat_messages
            WHERE id = ?
            """,
            message_id,
        )
        return cursor.fetchone()
    finally:
        connection.close()


def list_messages(before_id=None, limit=50):
    # Newest-first, like any chat history - the caller reverses for display
    # if it wants chronological order. `before_id` pages backward through
    # older history; omitted, this returns the most recent `limit` messages.
    #
    # LEFT JOINs the sender's profile_picture - same pattern dal/drive.py
    # already uses for an item's owner, rather than making the API expose a
    # general "look up any member by id" endpoint just to resolve avatars.
    # LEFT (not inner) JOIN so a message from a since-deleted member
    # (member_id is NULL - see the table's ON DELETE SET NULL) still comes
    # back with profile_picture simply NULL, not dropped from history.
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if before_id is None:
            cursor.execute(
                """
                SELECT c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes,
                       c.created_at AT TIME ZONE 'UTC' AS created_at, m.profile_picture
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
                SELECT c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes,
                       c.created_at AT TIME ZONE 'UTC' AS created_at, m.profile_picture
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


def delete_message(message_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_chat_messages WHERE id = ?", message_id)
    finally:
        connection.close()
