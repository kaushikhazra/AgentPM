"""Tests for rollup calculations."""

import pytest

from taskyn.core import (
    create_company,
    create_project,
    create_story,
    create_task,
    create_milestone,
    start_node,
    complete_node,
    log_time,
    get_node_rollup,
    get_milestone_rollup,
    get_project_rollup,
    RollupStats,
)
from taskyn.graph import update_node
from taskyn.exceptions import NotFoundError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_get_node_rollup_single_node(project):
    """Test rollup for a single node with no children."""
    story = create_story(
        project.id,
        title="Test Story",
        story_points=5,
    )
    log_time(story.id, duration_minutes=60)

    rollup = get_node_rollup(story.id)

    assert isinstance(rollup, RollupStats)
    assert rollup.total_nodes == 1
    assert rollup.total_time_minutes == 60
    assert rollup.story_points == 5
    assert rollup.completed_nodes == 0
    assert rollup.completion_percentage == 0.0


def test_get_node_rollup_with_children(project):
    """Test rollup for a story with tasks."""
    story = create_story(project.id, title="Test Story", story_points=8)

    task1 = create_task(story.id, title="Task 1", estimated_minutes=60)
    task2 = create_task(story.id, title="Task 2", estimated_minutes=120)
    task3 = create_task(story.id, title="Task 3", estimated_minutes=90)

    # Log time on tasks
    log_time(task1.id, duration_minutes=30)
    log_time(task2.id, duration_minutes=45)

    # Complete task1
    start_node(task1.id)
    complete_node(task1.id)

    rollup = get_node_rollup(story.id)

    assert rollup.total_nodes == 4  # story + 3 tasks
    assert rollup.total_time_minutes >= 75  # 30 + 45 (plus any from start/stop)
    assert rollup.estimated_time_minutes == 270  # 60 + 120 + 90
    assert rollup.completed_nodes == 1
    assert rollup.completion_percentage == 25.0  # 1/4 = 25%


def test_get_node_rollup_not_found(temp_db):
    """Test rollup for non-existent node."""
    with pytest.raises(NotFoundError):
        get_node_rollup("nonexistent")


def test_get_milestone_rollup(project):
    """Test rollup for a milestone."""
    milestone = create_milestone(project.id, name="Sprint 1")

    # Create stories in the milestone
    story1 = create_story(project.id, title="Story 1", milestone_id=milestone.id)
    story2 = create_story(project.id, title="Story 2", milestone_id=milestone.id)

    # Create tasks
    task1 = create_task(story1.id, title="Task 1", estimated_minutes=60)
    task2 = create_task(story2.id, title="Task 2", estimated_minutes=120)

    # Assign tasks to milestone too
    update_node(task1.id, milestone_id=milestone.id)
    update_node(task2.id, milestone_id=milestone.id)

    # Complete one story (stories need: backlog → ready → in_progress → done)
    update_node(story1.id, status="ready")
    start_node(story1.id)
    complete_node(story1.id)

    rollup = get_milestone_rollup(milestone.id)

    assert rollup.total_nodes == 4  # 2 stories + 2 tasks
    assert rollup.completed_nodes == 1
    assert rollup.estimated_time_minutes == 180


def test_get_milestone_rollup_empty(project):
    """Test rollup for an empty milestone."""
    milestone = create_milestone(project.id, name="Empty Sprint")

    rollup = get_milestone_rollup(milestone.id)

    assert rollup.total_nodes == 0
    assert rollup.completion_percentage == 0.0


def test_get_milestone_rollup_not_found(temp_db):
    """Test rollup for non-existent milestone."""
    with pytest.raises(NotFoundError):
        get_milestone_rollup("nonexistent")


def test_get_project_rollup(project):
    """Test rollup for entire project."""
    # Create some work items
    story1 = create_story(project.id, title="Story 1", story_points=5)
    story2 = create_story(project.id, title="Story 2", story_points=8)

    task1 = create_task(story1.id, title="Task 1", estimated_minutes=60)
    task2 = create_task(story1.id, title="Task 2", estimated_minutes=90)
    task3 = create_task(story2.id, title="Task 3", estimated_minutes=120)

    # Log time
    log_time(task1.id, duration_minutes=45)
    log_time(task2.id, duration_minutes=30)

    # Complete some items
    start_node(task1.id)
    complete_node(task1.id)

    rollup = get_project_rollup(project.id)

    assert rollup.total_nodes == 5  # 2 stories + 3 tasks
    assert rollup.completed_nodes == 1
    assert rollup.total_time_minutes >= 75
    assert rollup.estimated_time_minutes == 270
    assert rollup.story_points == 13  # 5 + 8


def test_get_project_rollup_empty(project):
    """Test rollup for empty project."""
    rollup = get_project_rollup(project.id)

    assert rollup.total_nodes == 0
    assert rollup.completion_percentage == 0.0


def test_get_project_rollup_not_found(temp_db):
    """Test rollup for non-existent project."""
    with pytest.raises(NotFoundError):
        get_project_rollup("nonexistent")


def test_rollup_with_blocked_nodes(project):
    """Test that blocked nodes are counted correctly."""
    story = create_story(project.id, title="Story")
    task1 = create_task(story.id, title="Task 1")
    task2 = create_task(story.id, title="Task 2")

    # Block task1
    start_node(task1.id)
    update_node(task1.id, status="blocked", blocked_reason="Waiting")

    # Start task2
    start_node(task2.id)

    rollup = get_node_rollup(story.id)

    assert rollup.blocked_nodes == 1
    assert rollup.in_progress_nodes == 1


def test_rollup_completion_percentage(project):
    """Test completion percentage calculation."""
    story = create_story(project.id, title="Story")
    task1 = create_task(story.id, title="Task 1")
    task2 = create_task(story.id, title="Task 2")
    task3 = create_task(story.id, title="Task 3")
    task4 = create_task(story.id, title="Task 4")

    # Complete 2 out of 5 (story + 4 tasks)
    start_node(task1.id)
    complete_node(task1.id)
    start_node(task2.id)
    complete_node(task2.id)

    rollup = get_node_rollup(story.id)

    assert rollup.total_nodes == 5
    assert rollup.completed_nodes == 2
    assert rollup.completion_percentage == 40.0  # 2/5 = 40%
