import hashlib
import secrets

from dal.db import get_connection

SESSION_LIFETIME_DAYS = 30


def _hash_token(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def create_session(member_id):
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO iblandbandet_sessions (token_hash, member_id, csrf_token, expires_at)
            VALUES (?, ?, ?, now() + interval '30 days')
            """,
            _hash_token(token), member_id, csrf_token,
        )
    finally:
        connection.close()
    return token, csrf_token


def get_session(token):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT member_id, csrf_token
            FROM iblandbandet_sessions
            WHERE token_hash = ? AND expires_at > now()
            """,
            _hash_token(token),
        )
        return cursor.fetchone()
    finally:
        connection.close()


def delete_session(token):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_sessions WHERE token_hash = ?", _hash_token(token))
    finally:
        connection.close()


def delete_sessions_for_member(member_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_sessions WHERE member_id = ?", member_id)
    finally:
        connection.close()
