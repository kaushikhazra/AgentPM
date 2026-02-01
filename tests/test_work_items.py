"""Tests for work items convenience API."""

import pytest

from taskyn.core import (
    create_company,
    create_project,
    create_story,
    create_task,
    get_story_with_tasks,
)
from taskyn.graph import get_node, get_parents
from taskyn.exceptions import NotFoundError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_create_story(project):
    """Test creating a story."""
    story = create_story(
        project.id,
        title="User Login Feature",
        description="Allow users to log in",
        priority="high",
        story_points=5,
    )

    assert story.id is not None
    assert story.node_type == "story"
    assert story.title == "User Login Feature"
    assert story.priority == "high"
    assert story.story_points == 5
    assert story.status == "backlog"  # Initial status for stories


def test_create_story_with_acceptance_criteria(project):
    """Test creating a story with acceptance criteria."""
    story = create_story(
        project.id,
        title="Feature",
        acceptance_criteria="- User can log in\n- User sees dashboard",
    )

    assert story.properties is not None
    assert story.properties["acceptance_criteria"] == "- User can log in\n- User sees dashboard"


def test_create_story_invalid_project(temp_db):
    """Test creating a story with invalid project."""
    with pytest.raises(NotFoundError):
        create_story("nonexistent", "Test Story")


def test_create_task(project):
    """Test creating a task under a story."""
    story = create_story(project.id, title="Parent Story")

    task = create_task(
        story.id,
        title="Implement login form",
        description="Create the HTML form",
        assignee="developer",
        estimated_minutes=120,
    )

    assert task.id is not None
    assert task.node_type == "task"
    assert task.title == "Implement login form"
    assert task.assignee == "developer"
    assert task.estimated_minutes == 120
    assert task.status == "todo"  # Initial status for tasks

    # Verify parent edge was created
    parents = get_parents(task.id)
    assert len(parents) == 1
    assert parents[0].id == story.id


def test_create_task_invalid_parent(temp_db):
    """Test creating a task with invalid parent."""
    with pytest.raises(NotFoundError):
        create_task("nonexistent", "Test Task")


def test_get_story_with_tasks(project):
    """Test getting a story with all its tasks."""
    story = create_story(project.id, title="Test Story")
    task1 = create_task(story.id, title="Task 1")
    task2 = create_task(story.id, title="Task 2")
    task3 = create_task(story.id, title="Task 3")

    result = get_story_with_tasks(story.id)

    assert result["story"].id == story.id
    assert len(result["tasks"]) == 3
    task_ids = [t.id for t in result["tasks"]]
    assert task1.id in task_ids
    assert task2.id in task_ids
    assert task3.id in task_ids


def test_get_story_with_tasks_not_found(temp_db):
    """Test getting a non-existent story."""
    with pytest.raises(NotFoundError):
        get_story_with_tasks("nonexistent")


def test_create_story_with_milestone(project):
    """Test creating a story assigned to a milestone."""
    from taskyn.core import create_milestone

    milestone = create_milestone(project.id, name="Sprint 1")

    story = create_story(
        project.id,
        title="Milestone Story",
        milestone_id=milestone.id,
    )

    assert story.milestone_id == milestone.id


def test_full_story_task_workflow(project):
    """Integration test: create story with tasks and verify structure."""
    # Create story
    story = create_story(
        project.id,
        title="User Authentication",
        description="Implement user auth system",
        story_points=8,
        actor="pm",
    )

    # Create tasks
    task1 = create_task(story.id, title="Design auth flow", estimated_minutes=60, actor="pm")
    task2 = create_task(story.id, title="Implement backend", estimated_minutes=240, actor="pm")
    task3 = create_task(story.id, title="Write tests", estimated_minutes=120, actor="pm")

    # Verify
    result = get_story_with_tasks(story.id)
    assert result["story"].story_points == 8
    assert len(result["tasks"]) == 3

    total_estimate = sum(t.estimated_minutes or 0 for t in result["tasks"])
    assert total_estimate == 420  # 60 + 240 + 120
