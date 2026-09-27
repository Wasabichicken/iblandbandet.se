from dal.db import get_connection


def list_children(parent_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if parent_id is None:
            cursor.execute(
                """
                SELECT i.id, i.parent_id, i.owner_id, i.name, i.is_directory,
                       i.storage_uuid, i.size_bytes, i.created_at,
                       m.profile_picture
                FROM iblandbandet_drive_items i
                LEFT JOIN iblandbandet_members m ON m.id = i.owner_id
                WHERE i.parent_id IS NULL
                ORDER BY NOT i.is_directory, lower(i.name)
                """
            )
        else:
            cursor.execute(
                """
                SELECT i.id, i.parent_id, i.owner_id, i.name, i.is_directory,
                       i.storage_uuid, i.size_bytes, i.created_at,
                       m.profile_picture
                FROM iblandbandet_drive_items i
                LEFT JOIN iblandbandet_members m ON m.id = i.owner_id
                WHERE i.parent_id = ?
                ORDER BY NOT i.is_directory, lower(i.name)
                """,
                parent_id,
            )
        return cursor.fetchall()
    finally:
        connection.close()


def get_item_by_id(item_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, parent_id, owner_id, name, is_directory, storage_uuid, size_bytes, created_at
            FROM iblandbandet_drive_items
            WHERE id = ?
            """,
            item_id,
        )
        return cursor.fetchone()
    finally:
        connection.close()


def create_directory(name, parent_id, owner_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_drive_items (parent_id, owner_id, name, is_directory)
            VALUES (?, ?, ?, TRUE)
            RETURNING id
            """,
            parent_id, owner_id, name,
        )
        return cursor.fetchone().id
    finally:
        connection.close()


def create_file(name, parent_id, owner_id, storage_uuid, size_bytes):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_drive_items
                (parent_id, owner_id, name, is_directory, storage_uuid, size_bytes)
            VALUES (?, ?, ?, FALSE, ?, ?)
            RETURNING id
            """,
            parent_id, owner_id, name, storage_uuid, size_bytes,
        )
        return cursor.fetchone().id
    finally:
        connection.close()


def delete_item(item_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_drive_items WHERE id = ?", item_id)
    finally:
        connection.close()


def rename_item(item_id, name):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE iblandbandet_drive_items SET name = ? WHERE id = ?", name, item_id)
    finally:
        connection.close()


def set_owner(item_id, new_owner_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE iblandbandet_drive_items SET owner_id = ? WHERE id = ?",
            new_owner_id, item_id,
        )
    finally:
        connection.close()


def move_item(item_id, new_parent_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE iblandbandet_drive_items SET parent_id = ? WHERE id = ?",
            new_parent_id, item_id,
        )
    finally:
        connection.close()


def list_subdirectories(parent_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if parent_id is None:
            cursor.execute(
                """
                SELECT id, name
                FROM iblandbandet_drive_items
                WHERE is_directory AND parent_id IS NULL
                ORDER BY lower(name)
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, name
                FROM iblandbandet_drive_items
                WHERE is_directory AND parent_id = ?
                ORDER BY lower(name)
                """,
                parent_id,
            )
        return cursor.fetchall()
    finally:
        connection.close()
