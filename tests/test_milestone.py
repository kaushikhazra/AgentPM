"""Tests for milestone operations."""

import pytest
from datetime import date

from taskyn.core import (
    create_company,
    create_project,
    create_milestone,
    get_milestone,
    list_milestones,
    update_milestone,
    complete_milestone,
    delete_milestone,
)
from taskyn.graph import create_node, update_node
from taskyn.exceptions import NotFoundError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_create_milestone(project):
    """Test creating a milestone."""
    milestone = create_milestone(
        project.id,
        name="MVP Release",
        description="First release",
        target_date=date(2025, 3, 1),
    )

    assert milestone.id is not None
    assert milestone.name == "MVP Release"
    assert milestone.status == "open"
    assert milestone.target_date == date(2025, 3, 1)


def test_create_milestone_invalid_project(temp_db):
    """Test creating a milestone with invalid project."""
    with pytest.raises(NotFoundError):
        create_milestone("nonexistent", name="Bad Milestone")


def test_get_milestone(project):
    """Test getting a milestone by ID."""
    created = create_milestone(project.id, name="Get Test")

    retrieved = get_milestone(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Get Test"


def test_list_milestones(project):
    """Test listing milestones."""
    create_milestone(project.id, name="Milestone 1")
    create_milestone(project.id, name="Milestone 2")

    milestones = list_milestones(project.id)

    assert len(milestones) == 2


def test_list_milestones_by_status(project):
    """Test listing milestones filtered by status."""
    m1 = create_milestone(project.id, name="Open Milestone")
    m2 = create_milestone(project.id, name="Completed Milestone")
    complete_milestone(m2.id)

    open_milestones = list_milestones(project.id, status="open")
    completed_milestones = list_milestones(project.id, status="completed")

    assert len(open_milestones) == 1
    assert len(completed_milestones) == 1


def test_update_milestone(project):
    """Test updating a milestone."""
    milestone = create_milestone(project.id, name="Original")

    updated = update_milestone(
        milestone.id,
        name="Updated",
        target_date=date(2025, 6, 1),
    )

    assert updated.name == "Updated"
    assert updated.target_date == date(2025, 6, 1)


def test_complete_milestone(project):
    """Test completing a milestone."""
    milestone = create_milestone(project.id, name="To Complete")

    completed = complete_milestone(milestone.id)

    assert completed.status == "completed"
    assert completed.completed_at is not None


def test_delete_milestone(project):
    """Test deleting a milestone."""
    milestone = create_milestone(project.id, name="To Delete")

    result = delete_milestone(milestone.id)

    assert result is True
    assert get_milestone(milestone.id) is None


def test_assign_node_to_milestone(project):
    """Test assigning a node to a milestone."""
    milestone = create_milestone(project.id, name="Sprint 1")
    node = create_node(project.id, node_type="story", title="Test Story")

    updated = update_node(node.id, milestone_id=milestone.id)

    assert updated.milestone_id == milestone.id
