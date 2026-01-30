"""Tests for activity logging."""

import pytest

from agentpm.core import (
    create_company,
    create_project,
    log_activity,
    list_activity,
    get_entity_activity,
    start_timer,
    stop_timer,
    tag_node,
)
from agentpm.graph import create_node, update_node, create_edge


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_log_activity(temp_db):
    """Test logging an activity entry."""
    activity = log_activity(
        entity_type="test",
        entity_id="123",
        action="test_action",
        old_value="old",
        new_value="new",
        actor="tester",
    )

    assert activity.id is not None
    assert activity.entity_type == "test"
    assert activity.action == "test_action"
    assert activity.actor == "tester"


def test_list_activity(temp_db):
    """Test listing activity entries."""
    log_activity("test", "1", "action1")
    log_activity("test", "2", "action2")
    log_activity("other", "3", "action3")

    all_activity = list_activity()
    assert len(all_activity) >= 3

    test_activity = list_activity(entity_type="test")
    assert len(test_activity) == 2


def test_get_entity_activity(temp_db):
    """Test getting activity for a specific entity."""
    log_activity("test", "entity1", "action1")
    log_activity("test", "entity1", "action2")
    log_activity("test", "entity2", "action3")

    entity1_activity = get_entity_activity("test", "entity1")

    assert len(entity1_activity) == 2


def test_node_creation_logs_activity(project):
    """Test that node creation logs activity."""
    node = create_node(project.id, node_type="task", title="Test Task", actor="tester")

    activity = get_entity_activity("node", node.id)

    assert len(activity) >= 1
    create_activity = [a for a in activity if a.action == "created"]
    assert len(create_activity) == 1
    assert create_activity[0].actor == "tester"


def test_status_change_logs_activity(project):
    """Test that status changes log activity."""
    node = create_node(project.id, node_type="task", title="Test Task")
    update_node(node.id, status="in_progress", actor="developer")

    activity = get_entity_activity("node", node.id)

    status_changes = [a for a in activity if a.action == "status_changed"]
    assert len(status_changes) == 1
    assert status_changes[0].old_value == "todo"
    assert status_changes[0].new_value == "in_progress"


def test_assignment_logs_activity(project):
    """Test that assignment changes log activity."""
    node = create_node(project.id, node_type="task", title="Test Task")
    update_node(node.id, assignee="developer", actor="pm")

    activity = get_entity_activity("node", node.id)

    assign_activity = [a for a in activity if a.action == "assigned"]
    assert len(assign_activity) == 1
    assert assign_activity[0].new_value == "developer"


def test_edge_creation_logs_activity(project):
    """Test that edge creation logs activity."""
    story = create_node(project.id, node_type="story", title="Story")
    task = create_node(project.id, node_type="task", title="Task")
    edge = create_edge(task.id, story.id, "parent", actor="pm")

    activity = get_entity_activity("edge", edge.id)

    assert len(activity) >= 1
    create_activity = [a for a in activity if a.action == "created"]
    assert len(create_activity) == 1


def test_time_tracking_logs_activity(project):
    """Test that time tracking logs activity."""
    node = create_node(project.id, node_type="task", title="Test Task")
    entry = start_timer(node.id, actor="developer")
    stop_timer(actor="developer")

    activity = list_activity(entity_type="time_entry")

    start_activity = [a for a in activity if a.action == "time_started"]
    stop_activity = [a for a in activity if a.action == "time_stopped"]

    assert len(start_activity) >= 1
    assert len(stop_activity) >= 1


def test_tagging_logs_activity(project):
    """Test that tagging logs activity."""
    node = create_node(project.id, node_type="task", title="Test Task")
    tag_node(node.id, "bug", actor="tester")

    activity = get_entity_activity("node", node.id)

    tag_activity = [a for a in activity if a.action == "tagged"]
    assert len(tag_activity) == 1
    assert tag_activity[0].new_value == "bug"


def test_activity_captures_full_workflow(project):
    """Integration test: verify activity captures full workflow."""
    # Create story
    story = create_node(project.id, node_type="story", title="Feature", actor="pm")

    # Create task
    task = create_node(project.id, node_type="task", title="Implement", actor="pm")

    # Link task to story
    create_edge(task.id, story.id, "parent", actor="pm")

    # Assign task
    update_node(task.id, assignee="developer", actor="pm")

    # Start work
    update_node(task.id, status="in_progress", actor="developer")
    start_timer(task.id, actor="developer")

    # Tag it
    tag_node(task.id, "backend", actor="developer")

    # Stop and complete
    stop_timer(actor="developer")
    update_node(task.id, status="done", actor="developer")

    # Check activity
    activity = get_entity_activity("node", task.id)

    # Should have: created, assigned, status_changed (2x), tagged
    actions = [a.action for a in activity]
    assert "created" in actions
    assert "assigned" in actions
    assert "status_changed" in actions
    assert "tagged" in actions
