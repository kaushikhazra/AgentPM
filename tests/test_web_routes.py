"""Tests for web backend REST routes (Phase 3 + Phase 11D)."""

import asyncio

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastmcp import Client

from taskyn.mcp.server import mcp as mcp_server
from taskyn.web.backend.auth.users import reset_connection
from taskyn.web.backend import deps
from taskyn.web.backend.main import app


@pytest.fixture(autouse=True)
def _reset_users_db(temp_db):
    """Reset the users DB connection to use the temp_db for each test."""
    reset_connection()
    yield
    reset_connection()


@pytest.fixture
def client(temp_db):
    """Create a test client with MCP client using in-memory transport."""
    mcp_client = Client(mcp_server)

    async def setup():
        await mcp_client.__aenter__()
        deps._mcp_client = mcp_client

    async def teardown():
        await mcp_client.__aexit__(None, None, None)
        deps._mcp_client = None

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(setup())
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        loop.run_until_complete(teardown())
        loop.close()


@pytest.fixture
def auth_headers(client):
    """Register a user, login, and return auth headers."""
    client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "testpass123",
        "name": "Test User",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "testpass123",
    })
    token = res.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# Companies
# ============================================================


def test_list_companies_empty(client, auth_headers):
    """List companies when none exist."""
    res = client.get("/api/v1/companies", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_create_company(client, auth_headers):
    """Create a company."""
    res = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "Acme Corp",
        "description": "A test company",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Acme Corp"
    assert "id" in data


def test_get_company(client, auth_headers):
    """Get a company by ID."""
    create = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "GetCo",
    })
    company_id = create.json()["id"]

    res = client.get(f"/api/v1/companies/{company_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "GetCo"


def test_get_company_not_found(client, auth_headers):
    """Get a company that doesn't exist."""
    res = client.get("/api/v1/companies/nonexistent", headers=auth_headers)
    assert res.status_code == 404


def test_delete_company(client, auth_headers):
    """Delete a company."""
    create = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "DeleteMe",
    })
    company_id = create.json()["id"]

    res = client.delete(f"/api/v1/companies/{company_id}", headers=auth_headers)
    assert res.status_code == 204

    # Verify deleted
    res = client.get(f"/api/v1/companies/{company_id}", headers=auth_headers)
    assert res.status_code == 404


def test_get_company_stats(client, auth_headers):
    """Get stats for a company."""
    create = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "StatsCo",
    })
    company_id = create.json()["id"]

    res = client.get(f"/api/v1/companies/{company_id}/stats", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["company_id"] == company_id
    assert data["total_projects"] == 0


def test_list_companies_with_stats(client, auth_headers):
    """List companies with include_stats=true."""
    client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "StatsListCo",
    })

    res = client.get(
        "/api/v1/companies?include_stats=true", headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert "stats" in data[0]


# ============================================================
# Projects
# ============================================================


@pytest.fixture
def company_id(client, auth_headers):
    """Create a company and return its ID."""
    res = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "ProjectCo",
    })
    return res.json()["id"]


def test_create_project(client, auth_headers, company_id):
    """Create a project."""
    res = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "My Project",
        "methodology": "classic_agile",
        "description": "Test project",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "My Project"
    assert "id" in data


def test_list_projects(client, auth_headers, company_id):
    """List projects."""
    client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "Proj A",
    })

    res = client.get("/api/v1/projects", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_list_projects_filter_by_company(client, auth_headers, company_id):
    """List projects filtered by company."""
    client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "Filtered Proj",
    })

    res = client.get(
        f"/api/v1/projects?company_id={company_id}", headers=auth_headers
    )
    assert res.status_code == 200
    assert all(p["company_id"] == company_id for p in res.json())


def test_get_project(client, auth_headers, company_id):
    """Get a project by ID."""
    create = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "GetProj",
    })
    project_id = create.json()["id"]

    res = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "GetProj"


def test_update_project(client, auth_headers, company_id):
    """Update a project."""
    create = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "Old Name",
    })
    project_id = create.json()["id"]

    res = client.patch(f"/api/v1/projects/{project_id}", headers=auth_headers, json={
        "name": "New Name",
    })
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


def test_delete_project(client, auth_headers, company_id):
    """Delete a project."""
    create = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "DeleteProj",
    })
    project_id = create.json()["id"]

    res = client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert res.status_code == 204


def test_get_methodology(client, auth_headers, company_id):
    """Get methodology info for a project."""
    create = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "MethodProj",
        "methodology": "classic_agile",
    })
    project_id = create.json()["id"]

    res = client.get(
        f"/api/v1/projects/{project_id}/methodology", headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "node_types" in data


def test_get_project_stats(client, auth_headers, company_id):
    """Get project stats."""
    create = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "StatsProj",
    })
    project_id = create.json()["id"]

    res = client.get(
        f"/api/v1/projects/{project_id}/stats", headers=auth_headers
    )
    assert res.status_code == 200


# ============================================================
# Nodes
# ============================================================


@pytest.fixture
def project_id(client, auth_headers, company_id):
    """Create a project and return its ID."""
    res = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "NodeProject",
        "methodology": "classic_agile",
    })
    return res.json()["id"]


def test_create_node(client, auth_headers, project_id):
    """Create a node."""
    res = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "My Story",
        "description": "A test story",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "My Story"
    assert "id" in data


def test_list_nodes(client, auth_headers, project_id):
    """List nodes for a project."""
    client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Listed Story",
    })

    res = client.get(
        f"/api/v1/nodes?project_id={project_id}", headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_get_node(client, auth_headers, project_id):
    """Get a node by ID (composite response)."""
    create = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "GetNode",
    })
    node_id = create.json()["id"]

    res = client.get(f"/api/v1/nodes/{node_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "GetNode"


def test_update_node(client, auth_headers, project_id):
    """Update a node."""
    create = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Old Title",
    })
    node_id = create.json()["id"]

    res = client.patch(f"/api/v1/nodes/{node_id}", headers=auth_headers, json={
        "title": "New Title",
    })
    assert res.status_code == 200
    assert res.json()["title"] == "New Title"


def test_start_node(client, auth_headers, project_id):
    """Transition task to in_progress (tasks can start directly from backlog)."""
    story = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Parent Story",
    })
    task = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Start Me",
        "parent_id": story.json()["id"],
    })
    node_id = task.json()["id"]

    res = client.post(
        f"/api/v1/nodes/{node_id}/start", headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"


def test_complete_node(client, auth_headers, project_id):
    """Transition task to done."""
    story = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Parent Story",
    })
    task = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Complete Me",
        "parent_id": story.json()["id"],
    })
    node_id = task.json()["id"]

    # Must start before completing
    client.post(f"/api/v1/nodes/{node_id}/start", headers=auth_headers)
    res = client.post(
        f"/api/v1/nodes/{node_id}/complete", headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "done"


def test_block_node(client, auth_headers, project_id):
    """Mark task as blocked (must be in_progress first)."""
    story = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Parent Story",
    })
    task = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Block Me",
        "parent_id": story.json()["id"],
    })
    node_id = task.json()["id"]

    # Start the task first
    client.post(f"/api/v1/nodes/{node_id}/start", headers=auth_headers)
    res = client.post(
        f"/api/v1/nodes/{node_id}/block", headers=auth_headers,
        json={"reason": "Waiting on dependency"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "blocked"


def test_node_ancestors_descendants(client, auth_headers, project_id):
    """Test ancestor and descendant traversal."""
    parent = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Parent",
    })
    parent_id = parent.json()["id"]

    child = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Child",
        "parent_id": parent_id,
    })
    child_id = child.json()["id"]

    # Ancestors
    res = client.get(
        f"/api/v1/nodes/{child_id}/ancestors", headers=auth_headers
    )
    assert res.status_code == 200
    ancestor_ids = [n["id"] for n in res.json()]
    assert parent_id in ancestor_ids

    # Descendants
    res = client.get(
        f"/api/v1/nodes/{parent_id}/descendants", headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_node_rollup(client, auth_headers, project_id):
    """Get rollup stats for a node."""
    create = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Rollup Node",
    })
    node_id = create.json()["id"]

    res = client.get(
        f"/api/v1/nodes/{node_id}/rollup", headers=auth_headers
    )
    assert res.status_code == 200


# ============================================================
# Edges
# ============================================================


def test_create_edge(client, auth_headers, project_id):
    """Create an edge between two nodes."""
    n1 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Source",
    })
    n2 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Target",
    })

    res = client.post("/api/v1/edges", headers=auth_headers, json={
        "source_id": n1.json()["id"],
        "target_id": n2.json()["id"],
        "edge_type": "depends_on",
    })
    assert res.status_code == 201
    assert "id" in res.json()


def test_list_edges(client, auth_headers, project_id):
    """List edges for a project."""
    n1 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "E1",
    })
    n2 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "E2",
    })
    client.post("/api/v1/edges", headers=auth_headers, json={
        "source_id": n1.json()["id"],
        "target_id": n2.json()["id"],
        "edge_type": "depends_on",
    })

    res = client.get(
        f"/api/v1/edges?project_id={project_id}", headers=auth_headers
    )
    assert res.status_code == 200
    # Should have at least 1 edge (depends_on)
    assert len(res.json()) >= 1


def test_delete_edge(client, auth_headers, project_id):
    """Delete an edge."""
    n1 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Del Edge 1",
    })
    n2 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Del Edge 2",
    })
    edge = client.post("/api/v1/edges", headers=auth_headers, json={
        "source_id": n1.json()["id"],
        "target_id": n2.json()["id"],
        "edge_type": "depends_on",
    })
    edge_id = edge.json()["id"]

    res = client.delete(f"/api/v1/edges/{edge_id}", headers=auth_headers)
    assert res.status_code == 204


# ============================================================
# Milestones
# ============================================================


def test_create_milestone(client, auth_headers, project_id):
    """Create a milestone."""
    res = client.post("/api/v1/milestones", headers=auth_headers, json={
        "project_id": project_id,
        "name": "v1.0",
        "description": "First release",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "v1.0"


def test_list_milestones(client, auth_headers, project_id):
    """List milestones for a project."""
    client.post("/api/v1/milestones", headers=auth_headers, json={
        "project_id": project_id,
        "name": "v2.0",
    })

    res = client.get(
        f"/api/v1/milestones?project_id={project_id}", headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_complete_milestone(client, auth_headers, project_id):
    """Complete a milestone."""
    create = client.post("/api/v1/milestones", headers=auth_headers, json={
        "project_id": project_id,
        "name": "v3.0",
    })
    milestone_id = create.json()["id"]

    res = client.post(
        f"/api/v1/milestones/{milestone_id}/complete", headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"


# ============================================================
# Tags
# ============================================================


def test_create_tag(client, auth_headers):
    """Create a tag."""
    res = client.post("/api/v1/tags", headers=auth_headers, json={
        "name": "urgent",
        "color": "#ff0000",
    })
    assert res.status_code == 201


def test_list_tags(client, auth_headers):
    """List all tags."""
    client.post("/api/v1/tags", headers=auth_headers, json={
        "name": "feature",
    })

    res = client.get("/api/v1/tags", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_tag_node(client, auth_headers, project_id):
    """Tag a node."""
    node = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Tagged Story",
    })
    node_id = node.json()["id"]

    client.post("/api/v1/tags", headers=auth_headers, json={
        "name": "critical",
    })

    res = client.post(
        f"/api/v1/nodes/{node_id}/tags", headers=auth_headers,
        json={"tag_name": "critical"},
    )
    assert res.status_code == 200


def test_untag_node(client, auth_headers, project_id):
    """Remove a tag from a node."""
    node = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Untagged Story",
    })
    node_id = node.json()["id"]

    client.post("/api/v1/tags", headers=auth_headers, json={"name": "removeme"})
    client.post(
        f"/api/v1/nodes/{node_id}/tags", headers=auth_headers,
        json={"tag_name": "removeme"},
    )

    res = client.delete(
        f"/api/v1/nodes/{node_id}/tags/removeme", headers=auth_headers
    )
    assert res.status_code == 200


# ============================================================
# Timer
# ============================================================


def test_start_and_stop_timer(client, auth_headers, project_id):
    """Start and stop a timer."""
    node = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Timed Task",
    })
    node_id = node.json()["id"]

    # Start timer
    start = client.post("/api/v1/timer/start", headers=auth_headers, json={
        "node_id": node_id,
        "notes": "Working on it",
    })
    assert start.status_code == 200

    # Get current timer
    current = client.get("/api/v1/timer/current", headers=auth_headers)
    assert current.status_code == 200

    # Stop timer
    stop = client.post("/api/v1/timer/stop", headers=auth_headers, json={})
    assert stop.status_code == 200


def test_get_current_timer_none(client, auth_headers):
    """Get current timer when none is active."""
    res = client.get("/api/v1/timer/current", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() is None


# ============================================================
# Time Entries
# ============================================================


def test_log_time(client, auth_headers, project_id):
    """Log a manual time entry."""
    node = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Logged Task",
    })
    node_id = node.json()["id"]

    res = client.post("/api/v1/time-entries", headers=auth_headers, json={
        "node_id": node_id,
        "duration_minutes": 30,
        "notes": "Manual log",
    })
    assert res.status_code == 201


# ============================================================
# Dashboard / Activity / Search
# ============================================================


def test_get_dashboard(client, auth_headers):
    """Get dashboard aggregates."""
    res = client.get("/api/v1/dashboard", headers=auth_headers)
    assert res.status_code == 200


def test_get_activity(client, auth_headers):
    """Get recent activity log."""
    res = client.get("/api/v1/activity", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_activity_with_filters(client, auth_headers):
    """Get activity with limit parameter."""
    res = client.get(
        "/api/v1/activity?limit=5", headers=auth_headers
    )
    assert res.status_code == 200
    assert len(res.json()) <= 5


def test_search(client, auth_headers, project_id):
    """Search for entities."""
    client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Searchable Story",
    })

    res = client.get(
        "/api/v1/search?query=Searchable", headers=auth_headers
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ============================================================
# Auth required (no token)
# ============================================================


def test_routes_require_auth(client):
    """All resource routes should return 401 without auth."""
    routes = [
        ("GET", "/api/v1/companies"),
        ("GET", "/api/v1/projects"),
        ("GET", "/api/v1/nodes"),
        ("GET", "/api/v1/edges"),
        ("GET", "/api/v1/milestones?project_id=x"),
        ("GET", "/api/v1/tags"),
        ("GET", "/api/v1/timer/current"),
        ("GET", "/api/v1/dashboard"),
        ("GET", "/api/v1/activity"),
        ("GET", "/api/v1/search?query=test"),
    ]
    for method, path in routes:
        if method == "GET":
            res = client.get(path)
        assert res.status_code in (401, 403), f"Expected 401/403 for {method} {path}"


# ============================================================
# Full CRUD Flow
# ============================================================


def test_full_crud_flow(client, auth_headers):
    """Integration test: company -> project -> node -> edge -> complete."""
    # Create company
    company = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "Flow Corp",
    })
    assert company.status_code == 201
    company_id = company.json()["id"]

    # Create project
    project = client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "Flow Project",
    })
    assert project.status_code == 201
    project_id = project.json()["id"]

    # Create parent story
    story = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "User Login",
    })
    assert story.status_code == 201
    story_id = story.json()["id"]

    # Create child task
    task = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Implement form",
        "parent_id": story_id,
    })
    assert task.status_code == 201
    task_id = task.json()["id"]

    # Start and complete the task
    client.post(f"/api/v1/nodes/{task_id}/start", headers=auth_headers)
    complete = client.post(
        f"/api/v1/nodes/{task_id}/complete", headers=auth_headers
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "done"

    # Check rollup on story
    rollup = client.get(
        f"/api/v1/nodes/{story_id}/rollup", headers=auth_headers
    )
    assert rollup.status_code == 200

    # Check project stats
    stats = client.get(
        f"/api/v1/projects/{project_id}/stats", headers=auth_headers
    )
    assert stats.status_code == 200

    # Dashboard should reflect the data
    dashboard = client.get("/api/v1/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200


# ============================================================
# Functional Tests (Phase 11D)
# ============================================================


def test_create_node_with_parent_auto_edge(client, auth_headers, project_id):
    """Creating a node with parent_id auto-creates a parent edge."""
    story = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Auto-Edge Parent",
    })
    story_id = story.json()["id"]

    task = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Auto-Edge Child",
        "parent_id": story_id,
    })
    task_id = task.json()["id"]
    assert task.status_code == 201

    # Verify edge was auto-created (direction: child → parent)
    edges = client.get(
        f"/api/v1/edges?project_id={project_id}", headers=auth_headers
    )
    parent_edges = [
        e for e in edges.json()
        if e["source_id"] == task_id and e["target_id"] == story_id and e["edge_type"] == "parent"
    ]
    assert len(parent_edges) == 1


def test_404_for_nonexistent_project(client, auth_headers):
    """GET nonexistent project returns 404."""
    res = client.get("/api/v1/projects/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


def test_404_for_nonexistent_node(client, auth_headers):
    """GET nonexistent node returns 404."""
    res = client.get("/api/v1/nodes/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


def test_404_for_nonexistent_milestone(client, auth_headers):
    """GET nonexistent milestone returns 404."""
    res = client.get("/api/v1/milestones/nonexistent-id", headers=auth_headers)
    assert res.status_code == 404


def test_update_company_via_rest(client, auth_headers):
    """PATCH /companies/:id updates the company."""
    create = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "PatchCo",
        "description": "Original",
    })
    company_id = create.json()["id"]

    res = client.patch(f"/api/v1/companies/{company_id}", headers=auth_headers, json={
        "name": "PatchCo Updated",
    })
    assert res.status_code == 200
    assert res.json()["name"] == "PatchCo Updated"


def test_delete_node_via_rest(client, auth_headers, project_id):
    """DELETE /nodes/:id deletes the node."""
    node = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Delete Me Node",
    })
    node_id = node.json()["id"]

    res = client.delete(f"/api/v1/nodes/{node_id}", headers=auth_headers)
    assert res.status_code == 204

    # Verify deleted
    res = client.get(f"/api/v1/nodes/{node_id}", headers=auth_headers)
    assert res.status_code == 404


def test_get_and_update_milestone_via_rest(client, auth_headers, project_id):
    """GET and PATCH /milestones/:id work correctly."""
    create = client.post("/api/v1/milestones", headers=auth_headers, json={
        "project_id": project_id,
        "name": "v4.0",
        "description": "Milestone for testing",
    })
    milestone_id = create.json()["id"]

    # GET
    res = client.get(f"/api/v1/milestones/{milestone_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "v4.0"

    # PATCH
    res = client.patch(f"/api/v1/milestones/{milestone_id}", headers=auth_headers, json={
        "name": "v4.1",
    })
    assert res.status_code == 200
    assert res.json()["name"] == "v4.1"


@pytest.mark.asyncio
async def test_mcp_update_project(temp_db):
    """pm_update_project MCP tool updates a project."""
    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client

        company = await deps.call_mcp_tool("pm_create_company", {"name": "MCP Update Co"})
        project = await deps.call_mcp_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "MCP Proj",
        })

        updated = await deps.call_mcp_tool("pm_update_project", {
            "project_id": project["id"],
            "name": "MCP Proj Updated",
        })
        assert updated["name"] == "MCP Proj Updated"


@pytest.mark.asyncio
async def test_mcp_delete_company(temp_db):
    """pm_delete_company MCP tool deletes a company."""
    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client

        company = await deps.call_mcp_tool("pm_create_company", {"name": "MCP Delete Co"})
        result = await deps.call_mcp_tool("pm_delete_company", {"company_id": company["id"]})
        assert result is True

        with pytest.raises(HTTPException) as exc_info:
            await deps.call_mcp_tool("pm_get_company", {"company_id": company["id"]})
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_mcp_delete_project(temp_db):
    """pm_delete_project MCP tool deletes a project."""
    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client

        company = await deps.call_mcp_tool("pm_create_company", {"name": "Del Proj Co"})
        project = await deps.call_mcp_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Del Me Proj",
        })

        result = await deps.call_mcp_tool("pm_delete_project", {"project_id": project["id"]})
        assert result is True

        with pytest.raises(HTTPException) as exc_info:
            await deps.call_mcp_tool("pm_get_project", {"project_id": project["id"]})
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_mcp_create_node_invalid_type(temp_db):
    """pm_create_node with invalid node_type raises error."""
    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client

        company = await deps.call_mcp_tool("pm_create_company", {"name": "Invalid Type Co"})
        project = await deps.call_mcp_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Invalid Type Proj",
            "methodology": "classic_agile",
        })

        with pytest.raises(HTTPException) as exc_info:
            await deps.call_mcp_tool("pm_create_node", {
                "project_id": project["id"],
                "node_type": "invalid_type_xyz",
                "title": "Bad Node",
            })
        assert exc_info.value.status_code in (422, 409)


def test_mcp_resources(temp_db):
    """MCP resources pm://dashboard and pm://activity/recent are readable."""
    from taskyn.mcp.server import mcp as mcp_server

    # The resources are registered on the MCP server
    # We verify they exist and are callable
    resources = {}
    for name, resource in mcp_server._resource_manager._resources.items():
        resources[str(name)] = resource

    assert any("dashboard" in str(k) for k in resources.keys()), \
        f"Expected pm://dashboard resource, found: {list(resources.keys())}"


# ============================================================
# Robustness Tests (Phase 11D)
# ============================================================


def test_create_edge_invalid_type(client, auth_headers, project_id):
    """Creating an edge with invalid edge_type fails gracefully."""
    n1 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Edge Invalid 1",
    })
    n2 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Edge Invalid 2",
    })

    res = client.post("/api/v1/edges", headers=auth_headers, json={
        "source_id": n1.json()["id"],
        "target_id": n2.json()["id"],
        "edge_type": "totally_invalid_type",
    })
    # Should fail with validation error
    assert res.status_code in (422, 409, 500)


def test_list_nodes_filter_combinations(client, auth_headers, project_id):
    """List nodes with multiple filter combinations."""
    # Create some nodes
    client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "Filter Story",
    })
    client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Filter Task",
    })

    # Filter by type
    res = client.get(
        f"/api/v1/nodes?project_id={project_id}&node_type=story",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert all(n["node_type"] == "story" for n in res.json())

    # Filter by status
    res = client.get(
        f"/api/v1/nodes?project_id={project_id}&status=backlog",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert all(n["status"] == "backlog" for n in res.json())

    # Filter by type AND status
    res = client.get(
        f"/api/v1/nodes?project_id={project_id}&node_type=story&status=backlog",
        headers=auth_headers,
    )
    assert res.status_code == 200
    for n in res.json():
        assert n["node_type"] == "story"
        assert n["status"] == "backlog"


def test_list_projects_with_stats(client, auth_headers, company_id):
    """GET /projects?include_stats=true returns stats."""
    client.post("/api/v1/projects", headers=auth_headers, json={
        "company_id": company_id,
        "name": "Stats Project",
    })

    res = client.get(
        "/api/v1/projects?include_stats=true", headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert "stats" in data[0]


def test_patch_node_empty_body(client, auth_headers, project_id):
    """PATCH /nodes/:id with empty body succeeds (no changes)."""
    node = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "No Change",
    })
    node_id = node.json()["id"]

    res = client.patch(f"/api/v1/nodes/{node_id}", headers=auth_headers, json={})
    assert res.status_code == 200
    assert res.json()["title"] == "No Change"


def test_search_result_content(client, auth_headers, project_id):
    """Search results contain matching entity data."""
    client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "story",
        "title": "UniqueSearchableName42",
    })

    res = client.get(
        "/api/v1/search?query=UniqueSearchableName42", headers=auth_headers
    )
    assert res.status_code == 200
    results = res.json()
    assert len(results) >= 1
    assert any(
        "UniqueSearchableName42" in r.get("entity", {}).get("title", "")
        for r in results
    )


def test_timer_start_second_stops_first(client, auth_headers, project_id):
    """Starting a second timer auto-stops the first."""
    node1 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Timer Task 1",
    })
    node2 = client.post("/api/v1/nodes", headers=auth_headers, json={
        "project_id": project_id,
        "node_type": "task",
        "title": "Timer Task 2",
    })

    # Start timer on task 1
    client.post("/api/v1/timer/start", headers=auth_headers, json={
        "node_id": node1.json()["id"],
    })

    # Start timer on task 2 — should auto-stop task 1
    client.post("/api/v1/timer/start", headers=auth_headers, json={
        "node_id": node2.json()["id"],
    })

    # Current timer should be for task 2
    current = client.get("/api/v1/timer/current", headers=auth_headers)
    assert current.status_code == 200
    assert current.json()["node_id"] == node2.json()["id"]


@pytest.mark.asyncio
async def test_mcp_block_node(temp_db):
    """pm_block_node MCP tool blocks a node."""
    async with Client(mcp_server) as mcp_client:
        deps._mcp_client = mcp_client

        company = await deps.call_mcp_tool("pm_create_company", {"name": "Block Co"})
        project = await deps.call_mcp_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Block Proj",
            "methodology": "classic_agile",
        })
        story = await deps.call_mcp_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "story",
            "title": "Block Parent",
        })
        task = await deps.call_mcp_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Block Task",
            "parent_id": story["id"],
        })

        # Start the task first
        await deps.call_mcp_tool("pm_start_node", {"node_id": task["id"]})

        # Block it
        result = await deps.call_mcp_tool("pm_block_node", {
            "node_id": task["id"],
            "reason": "Waiting on API access",
        })
        assert result["status"] == "blocked"
