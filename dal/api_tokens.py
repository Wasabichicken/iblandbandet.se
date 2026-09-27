import hashlib
import secrets

from dal.db import get_connection


def _hash_token(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def create_api_token(member_id):
    token = secrets.token_urlsafe(32)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO iblandbandet_api_tokens (token_hash, member_id) VALUES (?, ?)",
            _hash_token(token), member_id,
        )
    finally:
        connection.close()
    return token


def get_api_token_member_id(token):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT member_id FROM iblandbandet_api_tokens WHERE token_hash = ?",
            _hash_token(token),
        )
        row = cursor.fetchone()
        return row.member_id if row else None
    finally:
        connection.close()


def delete_api_token(token):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_api_tokens WHERE token_hash = ?", _hash_token(token))
    finally:
        connection.close()


def delete_other_api_tokens(member_id, keep_token):
    """Revoke every API token for this member except the one making the
    current request - used after a password change, so a leaked token
    doesn't survive it, without logging the caller's own device out.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM iblandbandet_api_tokens WHERE member_id = ? AND token_hash != ?",
            member_id, _hash_token(keep_token),
        )
    finally:
        connection.close()
