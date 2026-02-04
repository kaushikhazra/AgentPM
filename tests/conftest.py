"""Pytest configuration and fixtures for Taskyn tests."""

import os
import tempfile
from pathlib import Path

# Set env vars before any web backend imports (jwt.py validates at import time)
os.environ.setdefault("TASKYN_JWT_SECRET", "test-secret-key-for-pytest-minimum-32-chars")
os.environ.setdefault("TASKYN_RATE_LIMIT", "false")

import pytest

from taskyn.config import set_database_path
from taskyn.db.connection import close_connection, init_database


@pytest.fixture(autouse=True)
def reset_db_connection():
    """Reset database connection before each test."""
    close_connection()
    yield
    close_connection()


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_taskyn.db"
    set_database_path(str(db_path))
    init_database()
    yield db_path
    close_connection()
