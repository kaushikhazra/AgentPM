"""Tests for web backend auth (Phase 2)."""

import pytest
from fastapi.testclient import TestClient

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


def test_call_mcp_tool_success():
    """Test call_mcp_tool calls MCP tools correctly."""
    from taskyn.web.backend.deps import call_mcp_tool
    result = call_mcp_tool("pm_list_companies", {})
    assert isinstance(result, list)


def test_call_mcp_tool_not_found():
    """Test call_mcp_tool maps 'not found' to 404."""
    from fastapi import HTTPException
    from taskyn.web.backend.deps import call_mcp_tool

    with pytest.raises(HTTPException) as exc_info:
        call_mcp_tool("pm_get_company", {"company_id": "nonexistent"})
    assert exc_info.value.status_code == 404


def test_call_mcp_tool_unknown_tool():
    """Test call_mcp_tool with unknown tool name."""
    from fastapi import HTTPException
    from taskyn.web.backend.deps import call_mcp_tool

    with pytest.raises(HTTPException) as exc_info:
        call_mcp_tool("pm_nonexistent_tool", {})
    assert exc_info.value.status_code == 500
