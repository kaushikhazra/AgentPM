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

    _run_migrations()


def _run_migrations() -> None:
    """Run schema migrations for existing databases."""
    global _connection

    # Migration: add actual_time column to nodes
    columns = [
        row[1] for row in _connection.execute("PRAGMA table_info(nodes)").fetchall()
    ]
    if "actual_time" not in columns:
        _connection.execute("ALTER TABLE nodes ADD COLUMN actual_time INTEGER DEFAULT 0")
        _connection.commit()
        _backfill_actual_time()


def _backfill_actual_time() -> None:
    """One-time backfill of actual_time for all existing nodes."""
    global _connection

    # Step 1: Calculate own time for all nodes from time_entries (seconds)
    _connection.execute("""
        UPDATE nodes SET actual_time = COALESCE((
            SELECT SUM(
                CASE
                    WHEN te.started_at = te.ended_at THEN te.duration_minutes * 60
                    WHEN te.ended_at IS NOT NULL THEN CAST((julianday(te.ended_at) - julianday(te.started_at)) * 86400 AS INTEGER)
                    ELSE 0
                END
            )
            FROM time_entries te
            WHERE te.node_id = nodes.id AND te.ended_at IS NOT NULL
        ), 0)
    """)
    _connection.commit()

    # Step 2: Propagate bottom-up through parent edges
    # Each pass recalculates parent = own_entries_time + sum(children.actual_time)
    # Repeat until stable (handles multi-level hierarchies)
    for _ in range(10):  # Max 10 levels deep (practically never more than 3-4)
        prev_sum = _connection.execute(
            "SELECT COALESCE(SUM(actual_time), 0) FROM nodes"
        ).fetchone()[0]

        _connection.execute("""
            UPDATE nodes SET actual_time = (
                COALESCE((
                    SELECT SUM(
                        CASE
                            WHEN te.started_at = te.ended_at THEN te.duration_minutes * 60
                            WHEN te.ended_at IS NOT NULL THEN CAST((julianday(te.ended_at) - julianday(te.started_at)) * 86400 AS INTEGER)
                            ELSE 0
                        END
                    )
                    FROM time_entries te
                    WHERE te.node_id = nodes.id AND te.ended_at IS NOT NULL
                ), 0)
                +
                COALESCE((
                    SELECT SUM(child.actual_time)
                    FROM nodes child
                    JOIN edges e ON e.source_id = child.id
                    WHERE e.target_id = nodes.id AND e.edge_type = 'parent'
                ), 0)
            )
            WHERE id IN (
                SELECT DISTINCT e.target_id
                FROM edges e
                WHERE e.edge_type = 'parent'
            )
        """)
        _connection.commit()

        new_sum = _connection.execute(
            "SELECT COALESCE(SUM(actual_time), 0) FROM nodes"
        ).fetchone()[0]
        if new_sum == prev_sum:
            break


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
