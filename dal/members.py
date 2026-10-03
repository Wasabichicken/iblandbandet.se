import binascii
import hashlib
import hmac
import os

import pyodbc

from dal.db import get_connection

PBKDF2_ALGORITHM = 'sha256'
PBKDF2_ITERATIONS = 600_000


class DuplicateEmailError(Exception):
    pass


def hash_password(password):
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return binascii.hexlify(salt).decode('ascii'), binascii.hexlify(derived).decode('ascii')


def verify_password(password, salt_hex, hash_hex, iterations):
    salt = binascii.unhexlify(salt_hex)
    expected = binascii.unhexlify(hash_hex)
    derived = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(derived, expected)


def register_member(email, password, instruments, is_active=True, name=None):
    salt_hex, hash_hex = hash_password(password)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO iblandbandet_members
                    (email, password_hash, password_salt, password_iterations,
                     instruments, is_active, name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                email, hash_hex, salt_hex, PBKDF2_ITERATIONS, instruments, is_active, name,
            )
        except pyodbc.IntegrityError:
            raise DuplicateEmailError(email)
        return cursor.fetchone().id
    finally:
        connection.close()


def get_member_by_email(email):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, email, password_hash, password_salt, password_iterations,
                   instruments, description, is_active, profile_picture, is_admin, name
            FROM iblandbandet_members
            WHERE email = ?
            """,
            email,
        )
        return cursor.fetchone()
    finally:
        connection.close()


def get_member_by_id(member_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, email, password_hash, password_salt, password_iterations,
                   instruments, description, is_active, profile_picture, is_admin, name
            FROM iblandbandet_members
            WHERE id = ?
            """,
            member_id,
        )
        return cursor.fetchone()
    finally:
        connection.close()


def list_all_members():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, email, instruments, is_active, is_admin, profile_picture, name
            FROM iblandbandet_members
            ORDER BY email
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def update_profile(member_id, email, instruments, description, is_active, name):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE iblandbandet_members
                SET email = ?, instruments = ?, description = ?, is_active = ?, name = ?
                WHERE id = ?
                """,
                email, instruments, description, is_active, name, member_id,
            )
        except pyodbc.IntegrityError:
            raise DuplicateEmailError(email)
    finally:
        connection.close()


def update_profile_picture(member_id, url):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE iblandbandet_members SET profile_picture = ? WHERE id = ?",
            url, member_id,
        )
    finally:
        connection.close()


def admin_update_member(member_id, email, instruments, description, is_active, is_admin, name):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE iblandbandet_members
                SET email = ?, instruments = ?, description = ?,
                    is_active = ?, is_admin = ?, name = ?
                WHERE id = ?
                """,
                email, instruments, description, is_active, is_admin, name, member_id,
            )
        except pyodbc.IntegrityError:
            raise DuplicateEmailError(email)
    finally:
        connection.close()


def count_admins():
    # Used to stop the last remaining admin from deleting their own account
    # via self-service deletion (members/profile.cgi) - the admin panel's
    # own chicken-and-egg problem (no in-app way to promote the *first*
    # admin) means reaching zero admins has no in-app way back either.
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS n FROM iblandbandet_members WHERE is_admin")
        return cursor.fetchone().n
    finally:
        connection.close()


def delete_member(member_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM iblandbandet_members WHERE id = ?", member_id)
    finally:
        connection.close()


def update_password(member_id, new_password):
    salt_hex, hash_hex = hash_password(new_password)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE iblandbandet_members SET password_hash = ?, password_salt = ?, password_iterations = ? WHERE id = ?",
            hash_hex, salt_hex, PBKDF2_ITERATIONS, member_id,
        )
    finally:
        connection.close()
