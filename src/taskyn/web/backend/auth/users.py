"""User storage in SQLite.

This module manages the `users` table directly via sqlite3.
It does not import from taskyn.db to maintain web/core separation.
"""

import sqlite3
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel

from taskyn.config import get_database_path, ensure_db_directory


class User(BaseModel):
    """User model."""
    id: str
    email: str
    name: str
    created_at: datetime


class UserInDB(User):
    """User model with password hash (internal use only)."""
    password_hash: str


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _get_conn() -> sqlite3.Connection:
    """Get a connection to the database with users table ensured."""
    ensure_db_directory()
    db_path = get_database_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


# Module-level connection (lazy init)
_conn: sqlite3.Connection | None = None


def _db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _get_conn()
    return _conn


def create_user(email: str, password_hash: str, name: str) -> User:
    """Create a new user."""
    user_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    _db().execute(
        "INSERT INTO users (id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, email, password_hash, name, now),
    )
    _db().commit()
    return User(id=user_id, email=email, name=name, created_at=now)


def get_user(user_id: str) -> User | None:
    """Get a user by ID."""
    row = _db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    return User(id=row["id"], email=row["email"], name=row["name"], created_at=row["created_at"])


def get_user_by_email(email: str) -> UserInDB | None:
    """Get a user by email (includes password hash for verification)."""
    row = _db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    return UserInDB(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


def reset_connection() -> None:
    """Reset the module-level connection (used in testing)."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
