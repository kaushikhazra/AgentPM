"""Tests for caller-scoped actor override on MCP tools (CSA spec).

Tests validate _resolve_actor() logic and the end-to-end behavior when
core functions receive actor values resolved by the MCP tool layer.
"""

import pytest

from taskyn.core import (
    create_company,
    create_project,
    get_active_timer,
    get_active_timers,
    start_timer,
    stop_timer,
    start_node,
    complete_node,
)
from taskyn.graph import create_node
from taskyn.mcp.server import _resolve_actor, get_actor


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


@pytest.fixture
def task_a(project):
    """Create first test task."""
    return create_node(project.id, node_type="task", title="Task A")


@pytest.fixture
def task_b(project):
    """Create second test task."""
    return create_node(project.id, node_type="task", title="Task B")


# --- _resolve_actor unit tests ---


def test_resolve_actor_with_explicit_value():
    """Non-empty string overrides the transport default."""
    assert _resolve_actor("sub-1") == "sub-1"


def test_resolve_actor_with_none_falls_back():
    """None falls back to get_actor()."""
    assert _resolve_actor(None) == get_actor()


def test_resolve_actor_with_empty_string_falls_back():
    """Empty string falls back to get_actor() (D2)."""
    assert _resolve_actor("") == get_actor()


# --- pm_start_timer actor override (CSA-1) ---


def test_start_timer_with_explicit_actor(task_a):
    """start_timer with resolved actor creates entry under that actor."""
    entry = start_timer(task_a.id, actor=_resolve_actor("sub-1"))
    assert entry.actor == "sub-1"


def test_start_timer_no_actor_uses_default(task_a):
    """start_timer with resolved None uses get_actor() default."""
    entry = start_timer(task_a.id, actor=_resolve_actor(None))
    assert entry.actor == get_actor()


def test_start_timer_empty_actor_uses_default(task_a):
    """start_timer with resolved empty string uses get_actor() default."""
    entry = start_timer(task_a.id, actor=_resolve_actor(""))
    assert entry.actor == get_actor()


# --- Concurrent timers with different actors (CSA-5) ---


def test_concurrent_timers_different_actors(task_a, task_b):
    """Two different actors can run timers concurrently through same connection."""
    start_timer(task_a.id, actor=_resolve_actor("sub-1"))
    start_timer(task_b.id, actor=_resolve_actor("sub-2"))

    active = get_active_timers()
    actors = {e.actor for e in active}
    assert "sub-1" in actors
    assert "sub-2" in actors
    assert len(active) == 2


# --- pm_stop_timer actor override (CSA-2) ---


def test_stop_timer_with_explicit_actor(task_a, task_b):
    """stop_timer with resolved actor stops only that actor's timer."""
    start_timer(task_a.id, actor=_resolve_actor("sub-1"))
    start_timer(task_b.id, actor=_resolve_actor("sub-2"))

    stopped = stop_timer(actor=_resolve_actor("sub-1"))
    assert stopped is not None
    assert stopped.actor == "sub-1"

    active = get_active_timers()
    assert len(active) == 1
    assert active[0].actor == "sub-2"


# --- pm_start_node actor override (CSA-3) ---


def test_start_node_with_actor(task_a):
    """start_node with resolved actor starts timer under that actor."""
    start_node(task_a.id, actor=_resolve_actor("sub-1"))

    timer = get_active_timer(actor="sub-1")
    assert timer is not None
    assert timer.node_id == task_a.id
    assert timer.actor == "sub-1"


# --- pm_complete_node actor override (CSA-3) ---


def test_complete_node_with_actor(task_a, task_b):
    """complete_node with resolved actor stops only that actor's timer."""
    start_node(task_a.id, actor=_resolve_actor("sub-1"))
    start_node(task_b.id, actor=_resolve_actor("sub-2"))

    complete_node(task_a.id, actor=_resolve_actor("sub-1"))

    assert get_active_timer(actor="sub-1") is None

    timer = get_active_timer(actor="sub-2")
    assert timer is not None
    assert timer.node_id == task_b.id


# --- pm_get_active_timer actor override (CSA-4) ---


def test_get_active_timer_with_actor(task_a, task_b):
    """get_active_timer with resolved actor returns only that actor's timer."""
    start_timer(task_a.id, actor=_resolve_actor("sub-1"))
    start_timer(task_b.id, actor=_resolve_actor("sub-2"))

    timer1 = get_active_timer(actor=_resolve_actor("sub-1"))
    assert timer1 is not None
    assert timer1.actor == "sub-1"
    assert timer1.node_id == task_a.id

    timer2 = get_active_timer(actor=_resolve_actor("sub-2"))
    assert timer2 is not None
    assert timer2.actor == "sub-2"
    assert timer2.node_id == task_b.id
