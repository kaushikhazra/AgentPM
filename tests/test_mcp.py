"""Tests for MCP server using FastMCP client."""

import pytest
from fastmcp import Client

from agentpm.mcp.server import mcp


@pytest.fixture
def client(temp_db):
    """Create a FastMCP client for testing."""
    return Client(mcp)


def get_result(call_result):
    """Extract the actual result from CallToolResult."""
    if hasattr(call_result, 'structured_content') and call_result.structured_content:
        return call_result.structured_content.get('result', call_result.data)
    return call_result.data


@pytest.mark.asyncio
async def test_list_companies_empty(client):
    """Test listing companies when none exist."""
    async with client:
        result = get_result(await client.call_tool("pm_list_companies", {}))
        assert result == []


@pytest.mark.asyncio
async def test_create_company(client):
    """Test creating a company."""
    async with client:
        result = get_result(await client.call_tool("pm_create_company", {
            "name": "Test Company",
            "description": "A test company"
        }))
        assert result["name"] == "Test Company"
        assert result["description"] == "A test company"
        assert "id" in result


@pytest.mark.asyncio
async def test_get_company(client):
    """Test getting a company by ID."""
    async with client:
        # Create company
        created = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))

        # Get company
        result = get_result(await client.call_tool("pm_get_company", {"company_id": created["id"]}))
        assert result["name"] == "Test Co"
        assert "projects" in result


@pytest.mark.asyncio
async def test_create_project(client):
    """Test creating a project."""
    async with client:
        # Create company first
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))

        # Create project
        result = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project",
            "methodology": "classic_agile"
        }))
        assert result["name"] == "Test Project"
        assert result["methodology"] == "classic_agile"


@pytest.mark.asyncio
async def test_get_methodology_info(client):
    """Test getting methodology info."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))

        result = get_result(await client.call_tool("pm_get_methodology_info", {
            "project_id": project["id"]
        }))
        assert result["name"] == "classic_agile"
        assert "node_types" in result
        assert "story" in result["node_types"]
        assert "task" in result["node_types"]


@pytest.mark.asyncio
async def test_create_node(client):
    """Test creating a node."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))

        result = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "story",
            "title": "User Login Feature"
        }))
        assert result["title"] == "User Login Feature"
        assert result["node_type"] == "story"
        assert result["status"] == "backlog"


@pytest.mark.asyncio
async def test_create_node_with_parent(client):
    """Test creating a node with a parent edge."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))

        # Create story
        story = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "story",
            "title": "User Login"
        }))

        # Create task - parent edge will be created separately
        task = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Design form"
        }))

        # Create parent edge (task -> story)
        edge = get_result(await client.call_tool("pm_create_edge", {
            "source_id": task["id"],
            "target_id": story["id"],
            "edge_type": "parent"
        }))

        # Verify edge exists
        edges = get_result(await client.call_tool("pm_list_edges", {
            "source_id": task["id"],
            "edge_type": "parent"
        }))
        assert len(edges) == 1
        assert edges[0]["target_id"] == story["id"]


@pytest.mark.asyncio
async def test_node_workflow(client):
    """Test node start and complete workflow."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))
        task = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Test Task"
        }))

        # Start task
        started = get_result(await client.call_tool("pm_start_node", {"node_id": task["id"]}))
        assert started["status"] == "in_progress"

        # Complete task
        completed = get_result(await client.call_tool("pm_complete_node", {"node_id": task["id"]}))
        assert completed["status"] == "done"


@pytest.mark.asyncio
async def test_timer_workflow(client):
    """Test timer start and stop."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))
        task = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Test Task"
        }))

        # Start timer
        entry = get_result(await client.call_tool("pm_start_timer", {
            "node_id": task["id"],
            "notes": "Working on task"
        }))
        assert entry["node_id"] == task["id"]

        # Get active timer
        active = get_result(await client.call_tool("pm_get_active_timer", {}))
        assert active is not None
        assert active["node_id"] == task["id"]

        # Stop timer
        stopped = get_result(await client.call_tool("pm_stop_timer", {}))
        assert stopped is not None
        assert stopped["duration_minutes"] is not None


@pytest.mark.asyncio
async def test_log_time(client):
    """Test manual time logging."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))
        task = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Test Task"
        }))

        entry = get_result(await client.call_tool("pm_log_time", {
            "node_id": task["id"],
            "duration_minutes": 30,
            "notes": "Code review"
        }))
        assert entry["duration_minutes"] == 30


@pytest.mark.asyncio
async def test_dashboard(client):
    """Test dashboard retrieval."""
    async with client:
        result = get_result(await client.call_tool("pm_get_dashboard", {}))
        assert "in_progress_nodes" in result
        assert "blocked_nodes" in result
        assert "today_time_minutes" in result


@pytest.mark.asyncio
async def test_search(client):
    """Test search functionality."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Acme Corp"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Website Redesign"
        }))
        await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "story",
            "title": "Login Feature"
        })

        results = get_result(await client.call_tool("pm_search", {"query": "Login"}))
        assert len(results) > 0
        assert any(r["entity"]["title"] == "Login Feature" for r in results if "title" in r["entity"])


@pytest.mark.asyncio
async def test_tags(client):
    """Test tag operations."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))
        task = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Test Task"
        }))

        # Create tag
        tag = get_result(await client.call_tool("pm_create_tag", {
            "name": "urgent",
            "color": "#ff0000"
        }))
        assert tag["name"] == "urgent"

        # Tag node
        await client.call_tool("pm_tag_node", {
            "node_id": task["id"],
            "tag_name": "urgent"
        })

        # List tags
        tags = get_result(await client.call_tool("pm_list_tags", {}))
        assert len(tags) >= 1

        # Untag node
        result = get_result(await client.call_tool("pm_untag_node", {
            "node_id": task["id"],
            "tag_name": "urgent"
        }))
        assert result is True


@pytest.mark.asyncio
async def test_milestones(client):
    """Test milestone operations."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))

        # Create milestone
        milestone = get_result(await client.call_tool("pm_create_milestone", {
            "project_id": project["id"],
            "name": "Sprint 1",
            "target_date": "2025-06-01"
        }))
        assert milestone["name"] == "Sprint 1"

        # List milestones
        milestones = get_result(await client.call_tool("pm_list_milestones", {
            "project_id": project["id"]
        }))
        assert len(milestones) == 1

        # Complete milestone
        completed = get_result(await client.call_tool("pm_complete_milestone", {
            "milestone_id": milestone["id"]
        }))
        assert completed["status"] == "completed"


@pytest.mark.asyncio
async def test_edges(client):
    """Test edge operations."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))

        task1 = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Task 1"
        }))
        task2 = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Task 2"
        }))

        # Create edge (depends_on is valid for task->task)
        edge = get_result(await client.call_tool("pm_create_edge", {
            "source_id": task1["id"],
            "target_id": task2["id"],
            "edge_type": "depends_on"
        }))
        assert edge["edge_type"] == "depends_on"

        # List edges
        edges = get_result(await client.call_tool("pm_list_edges", {
            "source_id": task1["id"]
        }))
        assert len(edges) == 1

        # Delete edge
        deleted = get_result(await client.call_tool("pm_delete_edge", {
            "edge_id": edge["id"]
        }))
        assert deleted is True


@pytest.mark.asyncio
async def test_get_rollup(client):
    """Test rollup stats."""
    async with client:
        company = get_result(await client.call_tool("pm_create_company", {"name": "Test Co"}))
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Test Project"
        }))
        story = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "story",
            "title": "Test Story"
        }))

        rollup = get_result(await client.call_tool("pm_get_rollup", {"node_id": story["id"]}))
        assert "total_nodes" in rollup
        assert "completion_percentage" in rollup


@pytest.mark.asyncio
async def test_full_workflow(client):
    """Integration test: full project workflow via MCP."""
    async with client:
        # Create company
        company = get_result(await client.call_tool("pm_create_company", {
            "name": "ACME Corp"
        }))

        # Create project
        project = get_result(await client.call_tool("pm_create_project", {
            "company_id": company["id"],
            "name": "Website Redesign",
            "methodology": "classic_agile"
        }))

        # Create milestone
        milestone = get_result(await client.call_tool("pm_create_milestone", {
            "project_id": project["id"],
            "name": "Phase 1"
        }))

        # Create story
        story = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "story",
            "title": "User Login",
            "milestone_id": milestone["id"]
        }))

        # Create tasks under story
        task1 = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Design login form"
        }))
        # Create parent edge (task -> story)
        await client.call_tool("pm_create_edge", {
            "source_id": task1["id"],
            "target_id": story["id"],
            "edge_type": "parent"
        })

        task2 = get_result(await client.call_tool("pm_create_node", {
            "project_id": project["id"],
            "node_type": "task",
            "title": "Implement backend"
        }))
        # Create parent edge (task -> story)
        await client.call_tool("pm_create_edge", {
            "source_id": task2["id"],
            "target_id": story["id"],
            "edge_type": "parent"
        })

        # Start first task
        await client.call_tool("pm_start_node", {"node_id": task1["id"]})

        # Check dashboard
        dashboard = get_result(await client.call_tool("pm_get_dashboard", {}))
        assert len(dashboard["in_progress_nodes"]) >= 1

        # Complete first task
        await client.call_tool("pm_complete_node", {"node_id": task1["id"]})

        # Get project stats
        stats = get_result(await client.call_tool("pm_get_project_stats", {
            "project_id": project["id"]
        }))
        assert stats["completed_nodes"] >= 1

        # Get rollup for story
        rollup = get_result(await client.call_tool("pm_get_rollup", {"node_id": story["id"]}))
        assert rollup["total_nodes"] >= 2  # story + tasks

        # Check activity
        activity = get_result(await client.call_tool("pm_get_recent_activity", {"limit": 10}))
        assert len(activity) > 0
