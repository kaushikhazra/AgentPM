"""Pytest configuration and fixtures for Taskyn tests."""

import tempfile
from pathlib import Path

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
