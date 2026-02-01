"""Tests for node operations."""

import pytest

from taskyn.core import create_company, create_project
from taskyn.graph import create_node, get_node, list_nodes, update_node, delete_node
from taskyn.exceptions import NotFoundError, ValidationError, InvalidTransitionError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_create_node(project):
    """Test creating a node."""
    node = create_node(
        project.id,
        node_type="story",
        title="Test Story",
        description="A test story",
    )

    assert node.id is not None
    assert node.project_id == project.id
    assert node.node_type == "story"
    assert node.title == "Test Story"
    assert node.status == "backlog"  # Initial status for story


def test_create_task_node(project):
    """Test creating a task node."""
    node = create_node(project.id, node_type="task", title="Test Task")

    assert node.node_type == "task"
    assert node.status == "todo"  # Initial status for task


def test_create_node_invalid_type(project):
    """Test creating a node with invalid type."""
    with pytest.raises(ValidationError):
        create_node(project.id, node_type="invalid", title="Bad Node")


def test_create_node_invalid_project(temp_db):
    """Test creating a node with invalid project."""
    with pytest.raises(NotFoundError):
        create_node("nonexistent", node_type="story", title="Bad Node")


def test_get_node(project):
    """Test getting a node by ID."""
    created = create_node(project.id, node_type="story", title="Get Test")

    retrieved = get_node(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.title == "Get Test"


def test_get_node_not_found(temp_db):
    """Test getting a non-existent node."""
    result = get_node("nonexistent")
    assert result is None


def test_list_nodes(project):
    """Test listing nodes."""
    create_node(project.id, node_type="story", title="Story 1")
    create_node(project.id, node_type="story", title="Story 2")
    create_node(project.id, node_type="task", title="Task 1")

    all_nodes = list_nodes(project_id=project.id)
    assert len(all_nodes) == 3

    stories = list_nodes(project_id=project.id, node_type="story")
    assert len(stories) == 2

    tasks = list_nodes(project_id=project.id, node_type="task")
    assert len(tasks) == 1


def test_update_node_title(project):
    """Test updating node title."""
    node = create_node(project.id, node_type="story", title="Original")

    updated = update_node(node.id, title="Updated")

    assert updated.title == "Updated"


def test_update_node_status(project):
    """Test updating node status with valid transition."""
    node = create_node(project.id, node_type="story", title="Test")
    assert node.status == "backlog"

    updated = update_node(node.id, status="ready")
    assert updated.status == "ready"


def test_update_node_invalid_transition(project):
    """Test updating node status with invalid transition."""
    node = create_node(project.id, node_type="story", title="Test")
    assert node.status == "backlog"

    # Can't go directly from backlog to done
    with pytest.raises(ValidationError):
        update_node(node.id, status="done")


def test_update_node_to_done_sets_completed_at(project):
    """Test that updating to done status sets completed_at."""
    node = create_node(project.id, node_type="task", title="Test")

    # Progress through: todo -> in_progress -> done
    node = update_node(node.id, status="in_progress")
    node = update_node(node.id, status="done")

    assert node.completed_at is not None


def test_update_node_blocked_requires_reason(project):
    """Test that blocked status requires a reason."""
    node = create_node(project.id, node_type="task", title="Test")
    node = update_node(node.id, status="in_progress")

    # Should fail without reason
    with pytest.raises(ValidationError):
        update_node(node.id, status="blocked")

    # Should succeed with reason
    updated = update_node(node.id, status="blocked", blocked_reason="Waiting for API")
    assert updated.status == "blocked"
    assert updated.blocked_reason == "Waiting for API"


def test_delete_node(project):
    """Test deleting a node."""
    node = create_node(project.id, node_type="story", title="To Delete")

    result = delete_node(node.id)

    assert result is True
    assert get_node(node.id) is None


def test_delete_node_not_found(temp_db):
    """Test deleting a non-existent node."""
    result = delete_node("nonexistent")
    assert result is False


def test_node_full_lifecycle(project):
    """Test full node lifecycle through status transitions."""
    # Create task
    task = create_node(project.id, node_type="task", title="Full Lifecycle Task")
    assert task.status == "todo"

    # Start work
    task = update_node(task.id, status="in_progress")
    assert task.status == "in_progress"

    # Submit for review
    task = update_node(task.id, status="in_review")
    assert task.status == "in_review"

    # Complete
    task = update_node(task.id, status="done")
    assert task.status == "done"
    assert task.completed_at is not None
