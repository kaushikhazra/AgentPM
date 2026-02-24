"""Tests for time tracking operations."""

import pytest
import time

from taskyn.core import (
    create_company,
    create_project,
    start_timer,
    stop_timer,
    log_time,
    get_active_timer,
    get_active_timers,
    list_time_entries,
    get_time_total,
)
from taskyn.graph import create_node
from taskyn.exceptions import NotFoundError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


@pytest.fixture
def task(project):
    """Create a test task."""
    return create_node(project.id, node_type="task", title="Test Task")


def test_start_timer(task):
    """Test starting a timer."""
    entry = start_timer(task.id, notes="Working on it")

    assert entry.id is not None
    assert entry.node_id == task.id
    assert entry.started_at is not None
    assert entry.ended_at is None
    assert entry.notes == "Working on it"


def test_start_timer_invalid_node(temp_db):
    """Test starting a timer on invalid node."""
    with pytest.raises(NotFoundError):
        start_timer("nonexistent")


def test_stop_timer(task):
    """Test stopping a timer."""
    start_timer(task.id)

    stopped = stop_timer()

    assert stopped is not None
    assert stopped.ended_at is not None
    assert stopped.duration_minutes is not None
    assert stopped.duration_minutes >= 0


def test_stop_timer_no_active(temp_db):
    """Test stopping when no timer is active."""
    result = stop_timer()
    assert result is None


def test_auto_stop_on_new_start(project):
    """Test that starting a new timer auto-stops the previous one."""
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")

    # Start timer on task1
    entry1 = start_timer(task1.id)

    # Start timer on task2 - should auto-stop task1's timer
    entry2 = start_timer(task2.id)

    # Check task1's timer is stopped
    entries1 = list_time_entries(task1.id)
    assert len(entries1) == 1
    assert entries1[0].ended_at is not None

    # Check task2's timer is active
    active = get_active_timer()
    assert active is not None
    assert active.node_id == task2.id


def test_log_time(task):
    """Test logging manual time entry."""
    entry = log_time(task.id, duration_minutes=90, notes="Debugging session")

    assert entry.duration_minutes == 90
    assert entry.notes == "Debugging session"
    assert entry.ended_at is not None  # Manual entries are immediately closed


def test_get_active_timer(task):
    """Test getting the active timer."""
    # No active timer initially
    assert get_active_timer() is None

    # Start a timer
    start_timer(task.id)

    # Should now have an active timer
    active = get_active_timer()
    assert active is not None
    assert active.node_id == task.id


def test_list_time_entries(task):
    """Test listing time entries for a node."""
    log_time(task.id, duration_minutes=30)
    log_time(task.id, duration_minutes=60)

    entries = list_time_entries(task.id)

    assert len(entries) == 2


def test_get_time_total(task):
    """Test getting total time for a node."""
    log_time(task.id, duration_minutes=30)
    log_time(task.id, duration_minutes=60)
    log_time(task.id, duration_minutes=15)

    total = get_time_total(task.id)

    assert total == 105


def test_timer_workflow(task):
    """Test complete timer workflow: start -> stop -> verify."""
    # Start timer
    entry = start_timer(task.id, notes="Starting work")
    assert get_active_timer() is not None

    # Stop timer
    stopped = stop_timer()
    assert get_active_timer() is None
    assert stopped.duration_minutes is not None

    # Verify entry is in list
    entries = list_time_entries(task.id)
    assert len(entries) == 1
    assert entries[0].id == entry.id


# ============================================================
# Multi-Actor Concurrency Tests
# ============================================================


def test_multi_actor_concurrent_timers(project):
    """Agent-A and Agent-B both start timers. Neither kills the other."""
    task1 = create_node(project.id, node_type="task", title="Task A")
    task2 = create_node(project.id, node_type="task", title="Task B")

    entry_a = start_timer(task1.id, actor="agent-A")
    entry_b = start_timer(task2.id, actor="agent-B")

    # Both timers should be running
    active_a = get_active_timer(actor="agent-A")
    active_b = get_active_timer(actor="agent-B")
    assert active_a is not None
    assert active_b is not None
    assert active_a.node_id == task1.id
    assert active_b.node_id == task2.id

    # get_active_timers() should return both
    all_active = get_active_timers()
    assert len(all_active) == 2


def test_actor_scoped_auto_stop(project):
    """Agent-A starts timer on task-1, then task-2. Task-1 auto-stopped. Agent-B untouched."""
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")
    task3 = create_node(project.id, node_type="task", title="Task 3")

    # Agent-B starts a timer
    start_timer(task3.id, actor="agent-B")

    # Agent-A starts on task1, then switches to task2
    start_timer(task1.id, actor="agent-A")
    start_timer(task2.id, actor="agent-A")

    # Agent-A's task1 timer should be stopped
    entries1 = list_time_entries(task1.id)
    assert len(entries1) == 1
    assert entries1[0].ended_at is not None

    # Agent-A's active timer should be task2
    active_a = get_active_timer(actor="agent-A")
    assert active_a is not None
    assert active_a.node_id == task2.id

    # Agent-B's timer should be untouched
    active_b = get_active_timer(actor="agent-B")
    assert active_b is not None
    assert active_b.node_id == task3.id


def test_stop_timer_actor_scoping(project):
    """stop_timer(actor="A") only stops A's timer, not B's."""
    task1 = create_node(project.id, node_type="task", title="Task A")
    task2 = create_node(project.id, node_type="task", title="Task B")

    start_timer(task1.id, actor="agent-A")
    start_timer(task2.id, actor="agent-B")

    # Stop only agent-A's timer
    stopped = stop_timer(actor="agent-A")
    assert stopped is not None
    assert stopped.actor == "agent-A"

    # Agent-A has no active timer now
    assert get_active_timer(actor="agent-A") is None

    # Agent-B's timer still running
    active_b = get_active_timer(actor="agent-B")
    assert active_b is not None
    assert active_b.node_id == task2.id


def test_stop_timer_no_fallback(project):
    """Agent-A has no timer. stop_timer(actor="A") returns None — no fallback."""
    task1 = create_node(project.id, node_type="task", title="Task B")
    start_timer(task1.id, actor="agent-B")

    # Agent-A has no timer — should NOT stop agent-B's
    result = stop_timer(actor="agent-A")
    assert result is None

    # Agent-B's timer still running
    active_b = get_active_timer(actor="agent-B")
    assert active_b is not None


def test_get_active_timers_returns_all(project):
    """Three actors have timers. get_active_timers() returns all three."""
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")
    task3 = create_node(project.id, node_type="task", title="Task 3")

    start_timer(task1.id, actor="alpha")
    start_timer(task2.id, actor="beta")
    start_timer(task3.id, actor="gamma")

    all_active = get_active_timers()
    assert len(all_active) == 3
    actors = {t.actor for t in all_active}
    assert actors == {"alpha", "beta", "gamma"}


def test_start_timer_empty_actor_normalized(task):
    """start_timer(actor="") creates entry with actor=None."""
    entry = start_timer(task.id, actor="")
    assert entry.actor is None

    # Should be findable with actor=None
    active = get_active_timer(actor=None)
    assert active is not None
    assert active.id == entry.id

    # Should NOT be findable with actor=""
    # (get_active_timer doesn't normalize — queries WHERE actor IS "",
    #  but since no entries have actor="", returns None)


def test_cli_actor_round_trip(task):
    """start_timer(actor="cli") findable by get_active_timer(actor="cli"), not actor=None."""
    entry = start_timer(task.id, actor="cli")
    assert entry.actor == "cli"

    # Findable with actor="cli"
    active = get_active_timer(actor="cli")
    assert active is not None
    assert active.id == entry.id

    # NOT findable with actor=None
    assert get_active_timer(actor=None) is None

    # Stop with actor="cli" works
    stopped = stop_timer(actor="cli")
    assert stopped is not None
    assert stopped.actor == "cli"
    assert stopped.ended_at is not None
