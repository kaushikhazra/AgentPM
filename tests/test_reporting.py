"""Tests for dashboard, statistics, and search."""

import pytest
from datetime import datetime, timedelta

from taskyn.core import (
    create_company,
    create_project,
    create_story,
    create_task,
    create_milestone,
    start_node,
    complete_node,
    block_node,
    log_time,
    get_dashboard,
    get_project_stats,
    search,
    Dashboard,
    ProjectStats,
    SearchResult,
)
from taskyn.graph import get_node


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project", description="A test project")


def test_get_dashboard_empty(temp_db):
    """Test dashboard with no data."""
    dashboard = get_dashboard()

    assert isinstance(dashboard, Dashboard)
    assert dashboard.active_timer is None
    assert dashboard.active_timer_node is None
    assert len(dashboard.in_progress_nodes) == 0
    assert len(dashboard.blocked_nodes) == 0
    assert dashboard.today_time_minutes >= 0


def test_get_dashboard_with_active_timer(project):
    """Test dashboard with active timer."""
    story = create_story(project.id, title="Test Story")
    task = create_task(story.id, title="Active Task")

    start_node(task.id, actor="developer")

    dashboard = get_dashboard(actor="developer")

    assert dashboard.active_timer is not None
    assert dashboard.active_timer.node_id == task.id
    assert dashboard.active_timer_node is not None
    assert dashboard.active_timer_node.id == task.id


def test_get_dashboard_in_progress_nodes(project):
    """Test dashboard shows in-progress nodes."""
    story = create_story(project.id, title="Test Story")
    task1 = create_task(story.id, title="Task 1")
    task2 = create_task(story.id, title="Task 2")
    task3 = create_task(story.id, title="Task 3")

    start_node(task1.id)
    # Stop timer so we can start another
    complete_node(task1.id)

    start_node(task2.id)
    # Stop timer by starting another
    start_node(task3.id)

    dashboard = get_dashboard()

    # task2 is in_progress, task3 is in_progress (with active timer)
    # task1 is done
    in_progress_ids = [n.id for n in dashboard.in_progress_nodes]
    assert task2.id in in_progress_ids
    assert task3.id in in_progress_ids
    assert task1.id not in in_progress_ids


def test_get_dashboard_blocked_nodes(project):
    """Test dashboard shows blocked nodes."""
    story = create_story(project.id, title="Test Story")
    task1 = create_task(story.id, title="Blocked Task")
    task2 = create_task(story.id, title="Normal Task")

    start_node(task1.id)
    block_node(task1.id, reason="Waiting for API")

    dashboard = get_dashboard()

    blocked_ids = [n.id for n in dashboard.blocked_nodes]
    assert task1.id in blocked_ids
    assert task2.id not in blocked_ids


def test_get_dashboard_recent_activity(project):
    """Test dashboard includes recent activity."""
    story = create_story(project.id, title="Test Story", actor="pm")
    task = create_task(story.id, title="Test Task", actor="pm")
    start_node(task.id, actor="developer")

    dashboard = get_dashboard()

    assert len(dashboard.recent_activity) > 0
    # Most recent first
    actions = [a.action for a in dashboard.recent_activity]
    assert "created" in actions or "status_changed" in actions


def test_get_project_stats(project):
    """Test project statistics."""
    story1 = create_story(project.id, title="Story 1")
    story2 = create_story(project.id, title="Story 2")

    task1 = create_task(story1.id, title="Task 1")
    task2 = create_task(story1.id, title="Task 2")
    task3 = create_task(story2.id, title="Task 3")

    # Log some time
    log_time(task1.id, duration_minutes=60)
    log_time(task2.id, duration_minutes=30)

    # Complete some tasks
    start_node(task1.id)
    complete_node(task1.id)

    # Block a task
    start_node(task2.id)
    block_node(task2.id, reason="Blocked")

    stats = get_project_stats(project.id)

    assert isinstance(stats, ProjectStats)
    assert stats.total_nodes["story"] == 2
    assert stats.total_nodes["task"] == 3
    assert stats.nodes_by_status["done"] == 1
    assert stats.nodes_by_status["blocked"] == 1
    assert stats.time_total >= 90  # 60 + 30
    assert len(stats.blockers) == 1


def test_get_project_stats_with_milestones(project):
    """Test project statistics include milestone progress."""
    milestone1 = create_milestone(project.id, name="Sprint 1")
    milestone2 = create_milestone(project.id, name="Sprint 2")

    story = create_story(project.id, title="Story", milestone_id=milestone1.id)

    stats = get_project_stats(project.id)

    assert len(stats.milestone_progress) == 2
    milestone_names = [mp.milestone.name for mp in stats.milestone_progress]
    assert "Sprint 1" in milestone_names
    assert "Sprint 2" in milestone_names


def test_search_by_title(project):
    """Test searching by title."""
    story1 = create_story(project.id, title="Login Feature")
    story2 = create_story(project.id, title="Logout Feature")
    story3 = create_story(project.id, title="User Profile")

    results = search("Login")

    assert len(results) >= 1
    assert all(isinstance(r, SearchResult) for r in results)
    result_titles = [r.entity.title for r in results if hasattr(r.entity, "title")]
    assert "Login Feature" in result_titles


def test_search_by_description(project):
    """Test searching by description."""
    story = create_story(
        project.id,
        title="Feature",
        description="This allows users to authenticate",
    )

    results = search("authenticate")

    assert len(results) >= 1
    entity_ids = [r.entity.id for r in results]
    assert story.id in entity_ids


def test_search_milestones(project):
    """Test searching includes milestones."""
    milestone = create_milestone(
        project.id,
        name="Q1 Release",
        description="First quarter release",
    )

    results = search("Release", entity_types=["milestone"])

    assert len(results) >= 1
    assert all(r.entity_type == "milestone" for r in results)


def test_search_projects(temp_db):
    """Test searching includes projects."""
    company = create_company("Test Company")
    project = create_project(
        company.id,
        "Taskyn Development",
        description="Building the PM tool",
    )

    results = search("Taskyn", entity_types=["project"])

    assert len(results) >= 1
    assert all(r.entity_type == "project" for r in results)


def test_search_with_project_filter(project):
    """Test searching within a specific project."""
    story = create_story(project.id, title="Searchable Story")

    # Create another project with similar content
    company = create_company("Other Company")
    other_project = create_project(company.id, "Other Project")
    other_story = create_story(other_project.id, title="Searchable Story")

    results = search("Searchable", project_id=project.id)

    entity_ids = [r.entity.id for r in results if hasattr(r.entity, "id")]
    assert story.id in entity_ids
    # other_story should not be in results (filtered by project)


def test_search_relevance_ranking(project):
    """Test that title matches rank higher than description matches."""
    story1 = create_story(project.id, title="Login Feature")
    story2 = create_story(project.id, title="Other", description="Login is related")

    results = search("Login")

    # Title match should come first
    assert results[0].entity.id == story1.id
    assert results[0].relevance > results[1].relevance


def test_search_empty_results(project):
    """Test search with no matches."""
    create_story(project.id, title="Test Story")

    results = search("nonexistent_query_string_xyz")

    assert len(results) == 0


def test_search_match_context(project):
    """Test that search results include match context."""
    story = create_story(
        project.id,
        title="Feature",
        description="This is a long description that mentions authentication in the middle of the text",
    )

    results = search("authentication")

    assert len(results) >= 1
    result = next(r for r in results if r.entity.id == story.id)
    assert "authentication" in result.match_context.lower()


def test_dashboard_today_time(project):
    """Test that today's time is calculated correctly."""
    story = create_story(project.id, title="Test Story")
    task = create_task(story.id, title="Test Task")

    # Log time today
    log_time(task.id, duration_minutes=45)
    log_time(task.id, duration_minutes=30)

    dashboard = get_dashboard()

    assert dashboard.today_time_minutes >= 75
