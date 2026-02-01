"""Database connection management for Taskyn."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from taskyn.config import get_database_path, ensure_db_directory

# Global connection (single-threaded use)
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Get the database connection, creating it if necessary."""
    global _connection

    if _connection is None:
        ensure_db_directory()
        db_path = get_database_path()
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row

        # Enable foreign keys
        _connection.execute("PRAGMA foreign_keys = ON")

        # Initialize schema (safe to run multiple times due to IF NOT EXISTS)
        _init_schema()

    return _connection


def _init_schema() -> None:
    """Initialize the database schema (internal use)."""
    global _connection

    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema_sql = f.read()

    _connection.executescript(schema_sql)
    _connection.commit()


def close_connection() -> None:
    """Close the database connection."""
    global _connection

    if _connection is not None:
        _connection.close()
        _connection = None


def init_database() -> None:
    """Initialize the database schema.

    Note: This is called automatically on first connection.
    Can be called explicitly to ensure schema exists.
    """
    get_connection()  # Schema init happens automatically on connection


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute a SQL statement and return the cursor."""
    conn = get_connection()
    return conn.execute(sql, params)


def executemany(sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
    """Execute a SQL statement with multiple parameter sets."""
    conn = get_connection()
    return conn.executemany(sql, params_list)


def fetchone(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """Execute a SQL statement and fetch one result."""
    cursor = execute(sql, params)
    return cursor.fetchone()


def fetchall(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Execute a SQL statement and fetch all results."""
    cursor = execute(sql, params)
    return cursor.fetchall()


def commit() -> None:
    """Commit the current transaction."""
    conn = get_connection()
    conn.commit()
