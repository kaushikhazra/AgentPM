"""User storage in SQLite.

This module manages the `users` table directly via sqlite3.
It does not import from taskyn.db to maintain web/core separation.
"""

import sqlite3
import uuid
from contextlib import contextmanager
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

_initialized = False


@contextmanager
def _db():
    """Yield a per-call SQLite connection (thread-safe)."""
    global _initialized
    ensure_db_directory()
    db_path = get_database_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if not _initialized:
        conn.execute(_CREATE_TABLE)
        conn.commit()
        _initialized = True
    try:
        yield conn
    finally:
        conn.close()


def create_user(email: str, password_hash: str, name: str) -> User:
    """Create a new user."""
    user_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    with _db() as conn:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, password_hash, name, now),
        )
        conn.commit()
    return User(id=user_id, email=email, name=name, created_at=now)


def get_user(user_id: str) -> User | None:
    """Get a user by ID."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    return User(id=row["id"], email=row["email"], name=row["name"], created_at=row["created_at"])


def get_user_by_email(email: str) -> UserInDB | None:
    """Get a user by email (includes password hash for verification)."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
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
    """Reset the initialized flag (used in testing)."""
    global _initialized
    _initialized = False
