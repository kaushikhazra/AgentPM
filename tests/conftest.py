"""Pytest configuration and fixtures for Taskyn tests."""

import os
import tempfile
from pathlib import Path

# Set env vars before any web backend imports (jwt.py validates at import time)
os.environ.setdefault("TASKYN_JWT_SECRET", "test-secret-key-for-pytest-minimum-32-chars")
os.environ.setdefault("TASKYN_RATE_LIMIT", "false")
# Use stdio transport marker for tests (actual MCP client is injected by fixtures)
os.environ.setdefault("TASKYN_MCP_CMD", "python -m taskyn.mcp")

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


@pytest.fixture
def mcp_client_with_server(temp_db):
    """Create an MCP client with in-memory transport to the MCP server.

    This allows testing the full MCP flow without HTTP by using
    FastMCP's in-memory transport (pass server instance to Client).
    """
    import asyncio
    from fastmcp import Client
    from taskyn.mcp.server import mcp as mcp_server

    client = Client(mcp_server)

    # For sync tests, we'll provide a helper
    async def _setup():
        await client.__aenter__()
        return client

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_setup())
        yield client
    finally:
        loop.run_until_complete(client.__aexit__(None, None, None))
        loop.close()
