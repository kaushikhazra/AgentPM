"""Tests for web backend auth (Phase 2 + Phase 11D security)."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from jose import jwt

from taskyn.mcp.server import mcp as mcp_server
from taskyn.web.backend.auth.jwt import ALGORITHM, SECRET_KEY
from taskyn.web.backend.auth.users import reset_connection
from taskyn.web.backend.main import app


@pytest.fixture(autouse=True)
def _reset_users_db(temp_db):
    """Reset the users DB connection to use the temp_db for each test."""
    reset_connection()
    yield
    reset_connection()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ============================================================
# Registration
# ============================================================


def test_register_success(client):
    """Test successful registration."""
    res = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "securepass123",
        "name": "Alice",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["message"] == "Account created"
    assert "user_id" in data


def test_register_duplicate_email(client):
    """Test registration with existing email."""
    payload = {
        "email": "bob@example.com",
        "password": "password123",
        "name": "Bob",
    }
    client.post("/api/v1/auth/register", json=payload)
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409
    assert "Registration failed" in res.json()["detail"]


def test_register_invalid_email(client):
    """Test registration with invalid email format."""
    res = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "password123",
        "name": "Bad",
    })
    assert res.status_code == 422


def test_register_short_password(client):
    """Test registration with password shorter than 8 chars."""
    res = client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "password": "short",
        "name": "Short",
    })
    assert res.status_code == 422


# ============================================================
# Login
# ============================================================


def test_login_success(client):
    """Test successful login returns access token and sets cookie."""
    client.post("/api/v1/auth/register", json={
        "email": "carol@example.com",
        "password": "mypassword",
        "name": "Carol",
    })

    res = client.post("/api/v1/auth/login", json={
        "email": "carol@example.com",
        "password": "mypassword",
    })
    assert res.status_code == 200
    assert "accessToken" in res.json()
    assert "refresh_token" in res.cookies


def test_login_invalid_password(client):
    """Test login with wrong password."""
    client.post("/api/v1/auth/register", json={
        "email": "dave@example.com",
        "password": "correctpass",
        "name": "Dave",
    })

    res = client.post("/api/v1/auth/login", json={
        "email": "dave@example.com",
        "password": "wrongpass",
    })
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with email that doesn't exist."""
    res = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert res.status_code == 401


# ============================================================
# Token Refresh
# ============================================================


def test_refresh_success(client):
    """Test refreshing access token using cookie."""
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "eve@example.com",
        "password": "password123",
        "name": "Eve",
    })
    client.post("/api/v1/auth/login", json={
        "email": "eve@example.com",
        "password": "password123",
    })

    # Refresh using the cookie set by login
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == 200
    assert "accessToken" in res.json()


def test_refresh_no_cookie(client):
    """Test refresh without cookie."""
    # Use a fresh client without any cookies
    fresh_client = TestClient(app)
    res = fresh_client.post("/api/v1/auth/refresh")
    assert res.status_code == 401
    assert "No refresh token" in res.json()["detail"]


# ============================================================
# Logout
# ============================================================


def test_logout(client):
    """Test logout clears the refresh cookie."""
    # Register, login, then logout
    client.post("/api/v1/auth/register", json={
        "email": "frank@example.com",
        "password": "password123",
        "name": "Frank",
    })
    client.post("/api/v1/auth/login", json={
        "email": "frank@example.com",
        "password": "password123",
    })

    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.json()["message"] == "Logged out"


# ============================================================
# /auth/me (Protected)
# ============================================================


def test_me_authenticated(client):
    """Test /auth/me with valid token."""
    client.post("/api/v1/auth/register", json={
        "email": "grace@example.com",
        "password": "password123",
        "name": "Grace",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "grace@example.com",
        "password": "password123",
    })
    token = login_res.json()["accessToken"]

    res = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "grace@example.com"
    assert data["name"] == "Grace"
    assert "id" in data


def test_me_no_token(client):
    """Test /auth/me without token."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_invalid_token(client):
    """Test /auth/me with invalid token."""
    res = client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer invalidtoken",
    })
    assert res.status_code == 401


# ============================================================
# Full Auth Flow
# ============================================================


def test_full_auth_flow(client):
    """Integration test: register -> login -> me -> refresh -> logout."""
    # Register
    reg = client.post("/api/v1/auth/register", json={
        "email": "heidi@example.com",
        "password": "strongpass",
        "name": "Heidi",
    })
    assert reg.status_code == 201

    # Login
    login = client.post("/api/v1/auth/login", json={
        "email": "heidi@example.com",
        "password": "strongpass",
    })
    assert login.status_code == 200
    token = login.json()["accessToken"]

    # Get current user
    me = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert me.status_code == 200
    assert me.json()["name"] == "Heidi"

    # Refresh token
    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 200
    new_token = refresh.json()["accessToken"]
    assert new_token  # Got a valid token back

    # Use refreshed token
    me2 = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {new_token}",
    })
    assert me2.status_code == 200

    # Logout
    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200


# ============================================================
# deps.py — call_mcp_tool
# ============================================================


@pytest.mark.asyncio
async def test_call_mcp_tool_success(temp_db):
    """Test call_mcp_tool calls MCP tools correctly."""
    from taskyn.web.backend.deps import call_mcp_tool
    from taskyn.web.backend import deps

    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client
        try:
            result = await call_mcp_tool("pm_list_companies", {})
            assert isinstance(result, list)
        finally:
            deps._mcp_client = None


@pytest.mark.asyncio
async def test_call_mcp_tool_not_found(temp_db):
    """Test call_mcp_tool maps 'not found' to 404."""
    from fastapi import HTTPException
    from taskyn.web.backend.deps import call_mcp_tool
    from taskyn.web.backend import deps

    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client
        try:
            with pytest.raises(HTTPException) as exc_info:
                await call_mcp_tool("pm_get_company", {"company_id": "nonexistent"})
            assert exc_info.value.status_code == 404
        finally:
            deps._mcp_client = None


@pytest.mark.asyncio
async def test_call_mcp_tool_unknown_tool(temp_db):
    """Test call_mcp_tool with unknown tool name."""
    from fastapi import HTTPException
    from taskyn.web.backend.deps import call_mcp_tool
    from taskyn.web.backend import deps

    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client
        try:
            with pytest.raises((HTTPException, Exception)) as exc_info:
                await call_mcp_tool("pm_nonexistent_tool", {})
            if isinstance(exc_info.value, HTTPException):
                assert exc_info.value.status_code == 500
        finally:
            deps._mcp_client = None


# ============================================================
# Security Tests (CR-34, CR-35 — Phase 11D)
# ============================================================


def test_expired_access_token_rejected(client):
    """Expired JWT access token is rejected by /auth/me."""
    # Register user
    client.post("/api/v1/auth/register", json={
        "email": "expired@example.com",
        "password": "password123",
        "name": "Expired",
    })

    # Create a token that expired 1 hour ago
    expired_token = jwt.encode(
        {
            "sub": "fake-id",
            "email": "expired@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "jti": "expired-jti",
            "type": "access",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    res = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {expired_token}",
    })
    assert res.status_code == 401


def test_access_token_as_refresh_rejected(client):
    """Access token used as refresh token is rejected."""
    client.post("/api/v1/auth/register", json={
        "email": "swap@example.com",
        "password": "password123",
        "name": "Swap",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "swap@example.com",
        "password": "password123",
    })
    access_token = login_res.json()["accessToken"]

    # Try to use the access token as a refresh token (via cookie)
    client.cookies.set("refresh_token", access_token)
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == 401
    assert "Invalid token type" in res.json()["detail"]


def test_refresh_token_as_access_rejected(client):
    """Refresh token used as access token is rejected."""
    from taskyn.web.backend.auth.jwt import create_refresh_token

    refresh_token = create_refresh_token("fake-user-id")
    res = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {refresh_token}",
    })
    assert res.status_code == 401
    assert "Invalid token type" in res.json()["detail"]


def test_expired_refresh_token_rejected(client):
    """Expired refresh token is rejected."""
    expired_refresh = jwt.encode(
        {
            "sub": "fake-id",
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
            "iat": datetime.now(timezone.utc) - timedelta(days=8),
            "jti": "expired-refresh-jti",
            "type": "refresh",
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    client.cookies.set("refresh_token", expired_refresh)
    res = client.post("/api/v1/auth/refresh")
    assert res.status_code == 401


def test_unauthenticated_mutations_rejected(client):
    """POST/PATCH/DELETE on resource endpoints return 401 without auth."""
    mutation_routes = [
        ("POST", "/api/v1/companies", {"name": "Unauthed"}),
        ("PATCH", "/api/v1/companies/fake-id", {"name": "Updated"}),
        ("DELETE", "/api/v1/companies/fake-id", None),
        ("POST", "/api/v1/projects", {"company_id": "x", "name": "Unauthed"}),
        ("PATCH", "/api/v1/projects/fake-id", {"name": "Updated"}),
        ("DELETE", "/api/v1/projects/fake-id", None),
        ("POST", "/api/v1/nodes", {"project_id": "x", "node_type": "task", "title": "Unauthed"}),
        ("PATCH", "/api/v1/nodes/fake-id", {"title": "Updated"}),
        ("DELETE", "/api/v1/nodes/fake-id", None),
        ("POST", "/api/v1/nodes/fake-id/start", None),
        ("POST", "/api/v1/nodes/fake-id/complete", None),
        ("POST", "/api/v1/edges", {"source_id": "a", "target_id": "b", "edge_type": "depends_on"}),
        ("POST", "/api/v1/milestones", {"project_id": "x", "name": "Unauthed"}),
        ("POST", "/api/v1/timer/start", {"node_id": "x"}),
        ("POST", "/api/v1/timer/stop", {}),
    ]
    for method, path, body in mutation_routes:
        if method == "POST":
            res = client.post(path, json=body) if body else client.post(path)
        elif method == "PATCH":
            res = client.patch(path, json=body)
        elif method == "DELETE":
            res = client.delete(path)
        assert res.status_code in (401, 403), f"Expected 401/403 for {method} {path}, got {res.status_code}"
