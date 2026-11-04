"""
database/connection.py - the ONLY place that talks to MySQL directly.

Every query in the project goes through these helpers, and every helper uses
parameterised queries (%s placeholders) so user input can never change the SQL
(this prevents SQL injection).
"""
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal

import mysql.connector

from config import DB_CONFIG


def get_connection():
    """Open a new connection to the smart_college database."""
    return mysql.connector.connect(**DB_CONFIG, connection_timeout=10)


def _clean_value(value):
    """Convert MySQL-specific types into plain Python types that pandas/Streamlit like."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, timedelta):  # MySQL TIME columns come back as timedelta
        total_minutes = int(value.total_seconds() // 60)
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    return value


def _clean_row(row):
    return {key: _clean_value(val) for key, val in row.items()}


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of dictionaries (one per row)."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return [_clean_row(r) for r in rows]
    finally:
        conn.close()


def fetch_one(sql, params=None):
    """Run a SELECT and return the first row as a dictionary (or None)."""
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    """Run INSERT / UPDATE / DELETE. Returns (last_insert_id, affected_rows)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        result = (cur.lastrowid, cur.rowcount)
        cur.close()
        return result
    finally:
        conn.close()


def execute_many(sql, rows):
    """Run the same INSERT/UPDATE for many rows inside ONE transaction."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.executemany(sql, rows)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        count = cur.rowcount
        cur.close()
        return count
    finally:
        conn.close()


@contextmanager
def transaction():
    """
    Use for several statements that must succeed or fail together:

        with transaction() as cur:
            cur.execute(...)
            cur.execute(...)
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        yield cur
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection():
    """Return (ok, message). Used by check_setup.py and the Settings page."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return True, f"Connected to MySQL {version} (database: {DB_CONFIG['database']})"
    except mysql.connector.Error as err:
        return False, f"{err}"
