from dal.db import get_connection


def get_random_subtitle():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT subtitle FROM iblandbandet_subtitles ORDER BY random() LIMIT 1")
        row = cursor.fetchone()
        return row.subtitle if row else None
    finally:
        connection.close()


def list_all_subtitles():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, subtitle FROM iblandbandet_subtitles ORDER BY id")
        return cursor.fetchall()
    finally:
        connection.close()


def get_subtitle_by_id(subtitle_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, subtitle FROM iblandbandet_subtitles WHERE id = ?", subtitle_id)
        return cursor.fetchone()
    finally:
        connection.close()


def create_subtitle(subtitle):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO iblandbandet_subtitles (subtitle) VALUES (?)", subtitle)
    finally:
        connection.close()


def update_subtitle(subtitle_id, subtitle):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE iblandbandet_subtitles SET subtitle = ? WHERE id = ?", subtitle, subtitle_id)
    finally:
        connection.close()


def delete_subtitle(subtitle_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_subtitles WHERE id = ?", subtitle_id)
    finally:
        connection.close()
