import hashlib
import secrets

from dal.db import get_connection


def _hash_token(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def create_reset_token(member_id):
    token = secrets.token_urlsafe(32)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_password_resets WHERE member_id = ?", member_id)
        cursor.execute(
            """
            INSERT INTO iblandbandet_password_resets (token_hash, member_id, expires_at)
            VALUES (?, ?, now() + interval '60 minutes')
            """,
            _hash_token(token), member_id,
        )
    finally:
        connection.close()
    return token


def get_reset(token):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT member_id
            FROM iblandbandet_password_resets
            WHERE token_hash = ? AND expires_at > now() AND used_at IS NULL
            """,
            _hash_token(token),
        )
        return cursor.fetchone()
    finally:
        connection.close()


def consume_reset(token):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE iblandbandet_password_resets SET used_at = now() WHERE token_hash = ?", _hash_token(token))
    finally:
        connection.close()
