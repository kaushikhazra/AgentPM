"""Tests for workflow shortcuts."""

import pytest

from agentpm.core import (
    create_company,
    create_project,
    create_story,
    create_task,
    start_node,
    complete_node,
    block_node,
    unblock_node,
    submit_for_review,
    approve,
    reject,
    get_active_timer,
)
from agentpm.graph import get_node
from agentpm.exceptions import NotFoundError, ValidationError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


@pytest.fixture
def task(project):
    """Create a test task."""
    story = create_story(project.id, title="Test Story")
    return create_task(story.id, title="Test Task")


def test_start_node(task):
    """Test starting work on a node."""
    result = start_node(task.id, actor="developer")

    assert result.status == "in_progress"

    # Timer should be active
    active = get_active_timer()
    assert active is not None
    assert active.node_id == task.id


def test_complete_node(task):
    """Test completing a node."""
    # Start first
    start_node(task.id, actor="developer")
    assert get_active_timer() is not None

    # Complete
    result = complete_node(task.id, actor="developer")

    assert result.status == "done"
    assert result.completed_at is not None

    # Timer should be stopped
    active = get_active_timer()
    assert active is None


def test_block_node(task):
    """Test blocking a node."""
    start_node(task.id, actor="developer")

    result = block_node(task.id, reason="Waiting for API access", actor="developer")

    assert result.status == "blocked"
    assert result.blocked_reason == "Waiting for API access"


def test_unblock_node(task):
    """Test unblocking a node."""
    start_node(task.id)
    block_node(task.id, reason="Blocked")

    result = unblock_node(task.id, actor="developer")

    assert result.status == "in_progress"
    assert result.blocked_reason is None


def test_unblock_non_blocked_node(task):
    """Test unblocking a node that isn't blocked."""
    start_node(task.id)

    with pytest.raises(ValidationError):
        unblock_node(task.id)


def test_submit_for_review(task):
    """Test submitting a node for review."""
    start_node(task.id, actor="developer")

    result = submit_for_review(task.id, actor="developer")

    assert result.status == "in_review"

    # Timer should be stopped
    assert get_active_timer() is None


def test_approve(task):
    """Test approving a node in review."""
    start_node(task.id)
    submit_for_review(task.id)

    result = approve(task.id, actor="reviewer")

    assert result.status == "done"
    assert result.completed_at is not None


def test_approve_non_review_node(task):
    """Test approving a node that isn't in review."""
    start_node(task.id)

    with pytest.raises(ValidationError):
        approve(task.id)


def test_reject(task):
    """Test rejecting a node in review."""
    start_node(task.id)
    submit_for_review(task.id)

    result = reject(task.id, reason="Needs more tests", actor="reviewer")

    assert result.status == "in_progress"
    assert result.properties is not None
    assert result.properties.get("rejection_reason") == "Needs more tests"


def test_reject_non_review_node(task):
    """Test rejecting a node that isn't in review."""
    start_node(task.id)

    with pytest.raises(ValidationError):
        reject(task.id)


def test_start_invalid_node(temp_db):
    """Test starting an invalid node."""
    with pytest.raises(NotFoundError):
        start_node("nonexistent")


def test_full_workflow(task):
    """Integration test: full development workflow."""
    # Start work
    task = start_node(task.id, actor="developer")
    assert task.status == "in_progress"
    assert get_active_timer() is not None

    # Block due to dependency
    task = block_node(task.id, reason="Waiting for design", actor="developer")
    assert task.status == "blocked"

    # Unblock and continue
    task = unblock_node(task.id, actor="developer")
    assert task.status == "in_progress"

    # Submit for review
    task = submit_for_review(task.id, actor="developer")
    assert task.status == "in_review"

    # Reject (needs changes)
    task = reject(task.id, reason="Fix edge case", actor="reviewer")
    assert task.status == "in_progress"

    # Submit again
    task = submit_for_review(task.id, actor="developer")
    assert task.status == "in_review"

    # Approve
    task = approve(task.id, actor="reviewer")
    assert task.status == "done"
    assert task.completed_at is not None


def test_story_workflow(project):
    """Test workflow on a story (different statuses)."""
    from agentpm.graph import update_node as graph_update_node

    story = create_story(project.id, title="Test Story")

    # Stories in classic_agile need to go: backlog → ready → in_progress → done
    # First move to "ready"
    story = graph_update_node(story.id, status="ready")
    assert story.status == "ready"

    # Now we can start
    result = start_node(story.id, actor="pm")
    assert result.status == "in_progress"

    result = complete_node(story.id, actor="pm")
    assert result.status == "done"
