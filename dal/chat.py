from dal.db import get_connection

# created_at is always selected via AT TIME ZONE 'UTC' - unlike events/drive,
# chat has exactly one consumer (the API - see CHAT.md, never rendered on
# the website), so there's no naive-local-time website reader to stay
# compatible with. Every row this module returns is genuine UTC, full stop,
# same reasoning as list_all_events_utc() but without needing a separate
# naive-local variant alongside it, since nothing here ever needs one.

_MESSAGE_COLUMNS = """
    c.id, c.member_id, c.body, c.image_uuid, c.image_size_bytes, c.request_id,
    c.created_at AT TIME ZONE 'UTC' AS created_at,
    c.edited_at AT TIME ZONE 'UTC' AS edited_at, m.profile_picture, m.name,
    c.reply_to_id, c.reply_preview_name, c.reply_preview_body, c.reply_preview_is_image
"""


def create_message(member_id, body=None, image_uuid=None, image_size_bytes=None, request_id=None,
                    reply_to_id=None, reply_preview_name=None, reply_preview_body=None,
                    reply_preview_is_image=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_chat_messages
                (member_id, body, image_uuid, image_size_bytes, request_id,
                 reply_to_id, reply_preview_name, reply_preview_body, reply_preview_is_image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id, created_at AT TIME ZONE 'UTC' AS created_at
            """,
            member_id, body, image_uuid, image_size_bytes, request_id,
            reply_to_id, reply_preview_name, reply_preview_body, reply_preview_is_image,
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
            SELECT {columns}
            FROM iblandbandet_chat_messages c
            LEFT JOIN iblandbandet_members m ON m.id = c.member_id
            WHERE c.id = ?
            """.format(columns=_MESSAGE_COLUMNS),
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
            SELECT {columns}
            FROM iblandbandet_chat_messages c
            LEFT JOIN iblandbandet_members m ON m.id = c.member_id
            WHERE c.request_id = ?
            """.format(columns=_MESSAGE_COLUMNS),
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
                SELECT {columns}
                FROM iblandbandet_chat_messages c
                LEFT JOIN iblandbandet_members m ON m.id = c.member_id
                ORDER BY c.id DESC
                LIMIT ?
                """.format(columns=_MESSAGE_COLUMNS),
                limit,
            )
        else:
            cursor.execute(
                """
                SELECT {columns}
                FROM iblandbandet_chat_messages c
                LEFT JOIN iblandbandet_members m ON m.id = c.member_id
                WHERE c.id < ?
                ORDER BY c.id DESC
                LIMIT ?
                """.format(columns=_MESSAGE_COLUMNS),
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


def list_reactions_for_messages(message_ids):
    # Returns {message_id: [row, ...]}, grouped here in Python rather than
    # joined directly into list_messages()/get_message_by_id() - a reaction
    # is one-to-many per message, so joining it straight into those
    # (one-row-per-message) queries would multiply each message's row once
    # per reaction. Batching all messages' reactions into one query (rather
    # than one query per message) avoids an N+1 when listing a page of
    # history. LEFT JOIN so a reaction from a since-deleted member still
    # returns, with name=None.
    if not message_ids:
        return {}
    connection = get_connection()
    try:
        cursor = connection.cursor()
        # No prior dynamic IN (...) usage anywhere in dal/ - placeholders
        # are built to match the number of ids, then the ids themselves are
        # passed as individual positional params (not a single list/tuple
        # value), same calling convention as every other ? param here.
        placeholders = ','.join(['?'] * len(message_ids))
        cursor.execute(
            """
            SELECT r.message_id, r.member_id, r.emoji, m.name
            FROM iblandbandet_chat_reactions r
            LEFT JOIN iblandbandet_members m ON m.id = r.member_id
            WHERE r.message_id IN ({placeholders})
            ORDER BY r.id
            """.format(placeholders=placeholders),
            *message_ids,
        )
        grouped = {}
        for row in cursor.fetchall():
            grouped.setdefault(row.message_id, []).append(row)
        return grouped
    finally:
        connection.close()


def set_reaction(message_id, member_id, emoji):
    # First ON CONFLICT usage in this file - UPSERTs the member's reaction
    # on this message, replacing whatever emoji they'd previously picked
    # (UNIQUE(message_id, member_id) is what makes this a plain upsert
    # rather than a second row).
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_chat_reactions (message_id, member_id, emoji)
            VALUES (?, ?, ?)
            ON CONFLICT (message_id, member_id) DO UPDATE SET emoji = EXCLUDED.emoji, created_at = now()
            """,
            message_id, member_id, emoji,
        )
    finally:
        connection.close()


def remove_reaction(message_id, member_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM iblandbandet_chat_reactions WHERE message_id = ? AND member_id = ?",
            message_id, member_id,
        )
    finally:
        connection.close()
