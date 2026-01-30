"""Tests for database layer."""

import pytest

from agentpm.db.connection import get_connection, init_database, fetchall


def test_database_initialization(temp_db):
    """Test that database initializes correctly."""
    conn = get_connection()

    # Check tables exist
    tables = fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    table_names = [t["name"] for t in tables]

    assert "companies" in table_names
    assert "projects" in table_names
    assert "milestones" in table_names
    assert "nodes" in table_names
    assert "edges" in table_names
    assert "time_entries" in table_names
    assert "tags" in table_names
    assert "node_tags" in table_names
    assert "activity_log" in table_names


def test_foreign_keys_enabled(temp_db):
    """Test that foreign keys are enabled."""
    conn = get_connection()
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1
