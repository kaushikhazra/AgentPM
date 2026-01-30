"""Configuration management for AgentPM."""

import os
from pathlib import Path

# Default database path
DEFAULT_DB_DIR = Path.home() / ".agentpm"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "agentpm.db"

# Global database path (can be overridden)
_db_path: Path | None = None


def get_database_path() -> Path:
    """Get the current database path."""
    global _db_path

    if _db_path is not None:
        return _db_path

    # Check environment variable
    env_path = os.getenv("AGENTPM_DB")
    if env_path:
        return Path(env_path)

    return DEFAULT_DB_PATH


def set_database_path(path: str | Path) -> None:
    """Set the database path."""
    global _db_path
    _db_path = Path(path)


def ensure_db_directory() -> None:
    """Ensure the database directory exists."""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
