"""Unit tests for internal helpers in core/planning.py."""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from taskyn.core import create_company, create_project, create_plan
from taskyn.db.enums import Methodology
from taskyn.core.planning import (
    _get_max_display_order,
    _parse_date,
    _parse_datetime,
    _recompact_display_order,
    _shift_items_down,
    _validate_node_plannable,
)
from taskyn.db.connection import commit, execute, fetchall
from taskyn.exceptions import NotFoundError, ValidationError
from taskyn.graph import create_node


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------


def test_parse_date_from_date_object(temp_db):
    d = date(2026, 4, 1)
    assert _parse_date(d) == d


def test_parse_date_from_datetime_object(temp_db):
    dt = datetime(2026, 4, 1, 10, 30, 0, tzinfo=timezone.utc)
    assert _parse_date(dt) == date(2026, 4, 1)


def test_parse_date_from_iso_string(temp_db):
    assert _parse_date("2026-04-01") == date(2026, 4, 1)


def test_parse_date_from_datetime_string(temp_db):
    # SQLite sometimes returns "YYYY-MM-DDTHH:MM:SS" strings
    assert _parse_date("2026-04-01T10:30:00") == date(2026, 4, 1)


def test_parse_date_fallback_returns_today(temp_db):
    # None passes none of the isinstance checks → falls back to _today()
    result = _parse_date(None)
    assert isinstance(result, date)
    assert result == date.today()


# ---------------------------------------------------------------------------
# _parse_datetime
# ---------------------------------------------------------------------------


def test_parse_datetime_from_datetime_object(temp_db):
    dt = datetime(2026, 4, 1, 10, 30, 0, tzinfo=timezone.utc)
    assert _parse_datetime(dt) == dt


def test_parse_datetime_from_iso_string(temp_db):
    result = _parse_datetime("2026-04-01T10:30:00")
    assert result == datetime(2026, 4, 1, 10, 30, 0)


def test_parse_datetime_invalid_string_falls_back_to_now(temp_db):
    before = datetime.now(timezone.utc)
    result = _parse_datetime("not-a-valid-datetime")
    after = datetime.now(timezone.utc)
    # Result should be a datetime close to now (fallback path)
    assert isinstance(result, datetime)
    # Strip tz for comparison if needed — result may be naive or aware
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    assert before <= result <= after


# ---------------------------------------------------------------------------
# Fixtures shared by display-order helper tests
# ---------------------------------------------------------------------------


@pytest.fixture
def agile_setup(temp_db):
    """Return a (project, plan_id) pair with no items."""
    company = create_company("Test Co")
    project = create_project(company.id, "Agile Proj", Methodology.CLASSIC_AGILE)
    return project


@pytest.fixture
def plan_id_empty(agile_setup):
    """A plan with no items."""
    plan = create_plan(plan_date=date(2026, 4, 10), actor="alice")
    return plan["id"]


@pytest.fixture
def plan_id_with_two_tasks(agile_setup):
    """A plan with two task items at display_order 1 and 2."""
    t1 = create_node(agile_setup.id, node_type="task", title="Task A")
    t2 = create_node(agile_setup.id, node_type="task", title="Task B")
    plan = create_plan(
        plan_date=date(2026, 4, 11),
        actor="alice",
        items=[{"node_id": t1.id}, {"node_id": t2.id}],
    )
    return plan["id"]


# ---------------------------------------------------------------------------
# _get_max_display_order
# ---------------------------------------------------------------------------


def test_get_max_display_order_empty_plan(plan_id_empty):
    assert _get_max_display_order(plan_id_empty) == 0


def test_get_max_display_order_populated_plan(plan_id_with_two_tasks):
    assert _get_max_display_order(plan_id_with_two_tasks) == 2


# ---------------------------------------------------------------------------
# _shift_items_down
# ---------------------------------------------------------------------------


def test_shift_items_down_all_items(plan_id_with_two_tasks):
    """Shifting from position 1 moves both items (1→2, 2→3)."""
    _shift_items_down(plan_id_with_two_tasks, 1)
    commit()
    rows = fetchall(
        "SELECT display_order FROM plan_items WHERE plan_id = ? ORDER BY display_order ASC",
        (plan_id_with_two_tasks,),
    )
    assert [r["display_order"] for r in rows] == [2, 3]


def test_shift_items_down_only_at_or_after_position(plan_id_with_two_tasks):
    """Shifting from position 2 leaves position-1 item unchanged."""
    _shift_items_down(plan_id_with_two_tasks, 2)
    commit()
    rows = fetchall(
        "SELECT display_order FROM plan_items WHERE plan_id = ? ORDER BY display_order ASC",
        (plan_id_with_two_tasks,),
    )
    assert [r["display_order"] for r in rows] == [1, 3]


# ---------------------------------------------------------------------------
# _recompact_display_order
# ---------------------------------------------------------------------------


def test_recompact_display_order_fills_gaps(agile_setup):
    """After an artificial gap is introduced, recompact renumbers 1..N."""
    t1 = create_node(agile_setup.id, node_type="task", title="T1")
    t2 = create_node(agile_setup.id, node_type="task", title="T2")
    t3 = create_node(agile_setup.id, node_type="task", title="T3")
    plan = create_plan(
        plan_date=date(2026, 4, 12),
        actor="alice",
        items=[{"node_id": t1.id}, {"node_id": t2.id}, {"node_id": t3.id}],
    )
    plan_id = plan["id"]

    # Create a gap: set t3's display_order to 10
    execute(
        "UPDATE plan_items SET display_order = 10 WHERE plan_id = ? AND node_id = ?",
        (plan_id, t3.id),
    )
    commit()

    _recompact_display_order(plan_id)
    commit()

    rows = fetchall(
        "SELECT display_order FROM plan_items WHERE plan_id = ? ORDER BY display_order ASC",
        (plan_id,),
    )
    assert [r["display_order"] for r in rows] == [1, 2, 3]


def test_recompact_display_order_single_item(agile_setup):
    """Recompacting a plan with one item results in display_order = 1."""
    t1 = create_node(agile_setup.id, node_type="task", title="Solo")
    plan = create_plan(
        plan_date=date(2026, 4, 13),
        actor="alice",
        items=[{"node_id": t1.id}],
    )
    plan_id = plan["id"]

    execute(
        "UPDATE plan_items SET display_order = 99 WHERE plan_id = ?",
        (plan_id,),
    )
    commit()

    _recompact_display_order(plan_id)
    commit()

    rows = fetchall(
        "SELECT display_order FROM plan_items WHERE plan_id = ?",
        (plan_id,),
    )
    assert rows[0]["display_order"] == 1


# ---------------------------------------------------------------------------
# _validate_node_plannable
# ---------------------------------------------------------------------------


def test_validate_plannable_passes_for_task_in_classic_agile(temp_db):
    company = create_company("Co")
    project = create_project(company.id, "P", Methodology.CLASSIC_AGILE)
    task = create_node(project.id, node_type="task", title="Plannable Task")
    # Must not raise
    _validate_node_plannable(task.id)


def test_validate_plannable_raises_for_story_in_classic_agile(temp_db):
    company = create_company("Co")
    project = create_project(company.id, "P", Methodology.CLASSIC_AGILE)
    story = create_node(project.id, node_type="story", title="Non-plannable Story")
    with pytest.raises(ValidationError, match="not plannable"):
        _validate_node_plannable(story.id)


def test_validate_plannable_raises_for_missing_node(temp_db):
    with pytest.raises(NotFoundError):
        _validate_node_plannable("does-not-exist")


def test_validate_plannable_passes_when_project_unresolvable(temp_db):
    """A node whose project_id references a non-existent project passes silently."""
    node_id = uuid4().hex
    # Temporarily disable FK enforcement to insert an orphan node
    execute("PRAGMA foreign_keys = OFF")
    execute(
        """
        INSERT INTO nodes (id, project_id, node_type, title, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (node_id, "fake-project-id", "task", "Orphan", "todo"),
    )
    commit()
    execute("PRAGMA foreign_keys = ON")
    # Should NOT raise — project can't be resolved, so silently allowed
    _validate_node_plannable(node_id)
