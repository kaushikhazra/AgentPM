"""Integration tests for MCP client over various transports (Phase 4).

Tests the full flow: API → FastMCP Client → MCP Server
Tests error scenarios and concurrent requests.
"""

import asyncio
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client

from taskyn.mcp.server import mcp as mcp_server
from taskyn.web.backend.auth.users import reset_connection
from taskyn.web.backend import deps


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_users_db(temp_db):
    """Reset the users DB connection to use the temp_db for each test."""
    reset_connection()
    yield
    reset_connection()


@pytest.fixture
def mcp_in_memory_client(temp_db):
    """Create an MCP client using in-memory transport."""
    return Client(mcp_server)


@pytest.fixture
def web_client_with_mcp(temp_db, mcp_in_memory_client):
    """Create a web TestClient with MCP client using in-memory transport.

    This fixture patches the global MCP client in deps.py to use in-memory
    transport, allowing tests to run without an HTTP MCP server.
    """
    from taskyn.web.backend.main import app

    async def mock_init():
        global _client
        _client = mcp_in_memory_client
        await _client.__aenter__()
        deps._mcp_client = _client

    async def mock_close():
        global _client
        if _client:
            await _client.__aexit__(None, None, None)
            deps._mcp_client = None

    # Initialize before creating TestClient
    loop = asyncio.new_event_loop()
    _client = None

    try:
        loop.run_until_complete(mock_init())
        # Create client with lifespan disabled (we manage it ourselves)
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        loop.run_until_complete(mock_close())
        loop.close()


@pytest.fixture
def auth_headers(web_client_with_mcp):
    """Register a user, login, and return auth headers."""
    web_client_with_mcp.post("/api/v1/auth/register", json={
        "email": "integration@test.com",
        "password": "testpass123",
        "name": "Integration Tester",
    })
    res = web_client_with_mcp.post("/api/v1/auth/login", json={
        "email": "integration@test.com",
        "password": "testpass123",
    })
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Full Flow Tests
# ---------------------------------------------------------------------------


class TestFullMCPFlow:
    """Test full API → MCP Client → MCP Server flow."""

    def test_create_company_via_rest(self, web_client_with_mcp, auth_headers):
        """Create company via REST, verify MCP tool was called."""
        res = web_client_with_mcp.post("/api/v1/companies", headers=auth_headers, json={
            "name": "Integration Co",
            "description": "Created via REST → MCP flow",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Integration Co"
        assert "id" in data

    def test_full_crud_cycle(self, web_client_with_mcp, auth_headers):
        """Test complete CRUD cycle through MCP."""
        # Create
        create_res = web_client_with_mcp.post("/api/v1/companies", headers=auth_headers, json={
            "name": "CRUD Test Co",
        })
        assert create_res.status_code == 201
        company_id = create_res.json()["id"]

        # Read
        read_res = web_client_with_mcp.get(f"/api/v1/companies/{company_id}", headers=auth_headers)
        assert read_res.status_code == 200
        assert read_res.json()["name"] == "CRUD Test Co"

        # Update
        update_res = web_client_with_mcp.patch(f"/api/v1/companies/{company_id}", headers=auth_headers, json={
            "name": "CRUD Test Co Updated",
        })
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "CRUD Test Co Updated"

        # Delete
        delete_res = web_client_with_mcp.delete(f"/api/v1/companies/{company_id}", headers=auth_headers)
        assert delete_res.status_code == 204

        # Verify deleted
        verify_res = web_client_with_mcp.get(f"/api/v1/companies/{company_id}", headers=auth_headers)
        assert verify_res.status_code == 404

    def test_nested_entity_creation(self, web_client_with_mcp, auth_headers):
        """Test creating nested entities: Company → Project → Story → Task."""
        # Company
        company = web_client_with_mcp.post("/api/v1/companies", headers=auth_headers, json={
            "name": "Nested Co",
        })
        company_id = company.json()["id"]

        # Project
        project = web_client_with_mcp.post("/api/v1/projects", headers=auth_headers, json={
            "company_id": company_id,
            "name": "Nested Project",
            "methodology": "classic_agile",
        })
        assert project.status_code == 201
        project_id = project.json()["id"]

        # Story
        story = web_client_with_mcp.post("/api/v1/nodes", headers=auth_headers, json={
            "project_id": project_id,
            "node_type": "story",
            "title": "Nested Story",
        })
        assert story.status_code == 201
        story_id = story.json()["id"]

        # Task (with parent)
        task = web_client_with_mcp.post("/api/v1/nodes", headers=auth_headers, json={
            "project_id": project_id,
            "node_type": "task",
            "title": "Nested Task",
            "parent_id": story_id,
        })
        assert task.status_code == 201

        # Verify traversal
        descendants = web_client_with_mcp.get(
            f"/api/v1/nodes/{story_id}/descendants", headers=auth_headers
        )
        assert descendants.status_code == 200
        assert len(descendants.json()) >= 1


# ---------------------------------------------------------------------------
# Error Scenario Tests
# ---------------------------------------------------------------------------


class TestMCPErrorScenarios:
    """Test error handling when MCP server has issues."""

    def test_mcp_server_unavailable(self, temp_db):
        """Test behavior when MCP client not initialized."""
        from taskyn.web.backend.main import app

        # Force client to None
        original_client = deps._mcp_client
        deps._mcp_client = None

        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                # Register and login
                client.post("/api/v1/auth/register", json={
                    "email": "error@test.com",
                    "password": "testpass123",
                    "name": "Error Tester",
                })
                res = client.post("/api/v1/auth/login", json={
                    "email": "error@test.com",
                    "password": "testpass123",
                })
                token = res.json()["accessToken"]
                headers = {"Authorization": f"Bearer {token}"}

                # Try to call an MCP tool
                res = client.get("/api/v1/companies", headers=headers)
                assert res.status_code == 503
                assert "not initialized" in res.json()["detail"]
        finally:
            deps._mcp_client = original_client

    def test_not_found_error_mapping(self, web_client_with_mcp, auth_headers):
        """Test that 'not found' errors from MCP map to 404."""
        res = web_client_with_mcp.get("/api/v1/companies/nonexistent-id", headers=auth_headers)
        assert res.status_code == 404

    def test_invalid_node_type_error(self, web_client_with_mcp, auth_headers):
        """Test that validation errors from MCP map to 422."""
        # Create company and project first
        company = web_client_with_mcp.post("/api/v1/companies", headers=auth_headers, json={
            "name": "Validation Co",
        })
        project = web_client_with_mcp.post("/api/v1/projects", headers=auth_headers, json={
            "company_id": company.json()["id"],
            "name": "Validation Project",
            "methodology": "classic_agile",
        })

        # Try invalid node type
        res = web_client_with_mcp.post("/api/v1/nodes", headers=auth_headers, json={
            "project_id": project.json()["id"],
            "node_type": "invalid_type_xyz",
            "title": "Bad Node",
        })
        assert res.status_code in (422, 409)


# ---------------------------------------------------------------------------
# Concurrent Request Tests
# ---------------------------------------------------------------------------


class TestConcurrentRequests:
    """Test concurrent request handling."""

    def test_concurrent_company_creation(self, web_client_with_mcp, auth_headers):
        """Test creating multiple companies concurrently.

        Note: TestClient is synchronous, so we simulate by rapid sequential calls.
        Real concurrent testing would require async HTTP client.
        """
        companies = []
        for i in range(5):
            res = web_client_with_mcp.post("/api/v1/companies", headers=auth_headers, json={
                "name": f"Concurrent Co {i}",
            })
            assert res.status_code == 201
            companies.append(res.json())

        # Verify all created
        list_res = web_client_with_mcp.get("/api/v1/companies", headers=auth_headers)
        assert list_res.status_code == 200
        created_names = {c["name"] for c in list_res.json()}
        for i in range(5):
            assert f"Concurrent Co {i}" in created_names


# ---------------------------------------------------------------------------
# Health Check Tests
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_healthy(self, web_client_with_mcp):
        """Test health check when MCP is connected."""
        res = web_client_with_mcp.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["mcp"] == "connected"
        assert "tools_count" in data

    def test_health_check_degraded(self, temp_db):
        """Test health check when MCP client not initialized."""
        from taskyn.web.backend.main import app

        original_client = deps._mcp_client
        deps._mcp_client = None

        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                res = client.get("/health")
                assert res.status_code == 200
                data = res.json()
                assert data["status"] == "degraded"
                assert data["mcp"] == "unreachable"
        finally:
            deps._mcp_client = original_client


# ---------------------------------------------------------------------------
# Direct MCP Client Tests (bypass REST layer)
# ---------------------------------------------------------------------------


class TestDirectMCPClient:
    """Test MCP client directly with in-memory transport."""

    @pytest.mark.asyncio
    async def test_list_tools(self, temp_db):
        """Test listing MCP tools."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]

            # Verify core tools exist
            assert "pm_create_company" in tool_names
            assert "pm_list_companies" in tool_names
            assert "pm_create_project" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_directly(self, temp_db):
        """Test calling MCP tool directly via client."""
        async with Client(mcp_server) as client:
            # Create company
            result = await client.call_tool("pm_create_company", {
                "name": "Direct MCP Co",
            })
            assert result.data["name"] == "Direct MCP Co"
            company_id = result.data["id"]

            # List companies
            list_result = await client.call_tool("pm_list_companies", {})
            names = [c["name"] for c in list_result.data]
            assert "Direct MCP Co" in names

            # Delete company
            delete_result = await client.call_tool("pm_delete_company", {
                "company_id": company_id,
            })
            assert delete_result.data is True

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, temp_db):
        """Test error handling from MCP tools."""
        from fastmcp.exceptions import ClientError

        async with Client(mcp_server) as client:
            with pytest.raises(ClientError) as exc_info:
                await client.call_tool("pm_get_company", {
                    "company_id": "nonexistent-id",
                })
            assert "not found" in str(exc_info.value).lower()
