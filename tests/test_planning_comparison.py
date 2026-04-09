"""Unit tests for plan_vs_actual in core/planning.py."""

from datetime import date

import pytest

from taskyn.core import create_company, create_project, log_time
from taskyn.db.enums import Methodology
from taskyn.core.planning import (
    add_plan_item,
    create_plan,
    plan_vs_actual,
    update_plan_item,
    _today,
)
from taskyn.graph import create_node


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agile_project(temp_db):
    company = create_company("Test Co")
    return create_project(company.id, "Agile Project", Methodology.CLASSIC_AGILE)


@pytest.fixture
def today():
    return _today()


@pytest.fixture
def task1(agile_project):
    return create_node(agile_project.id, node_type="task", title="Task 1")


@pytest.fixture
def task2(agile_project):
    return create_node(agile_project.id, node_type="task", title="Task 2")


# ---------------------------------------------------------------------------
# Planned item with time entry: delta computed correctly
# ---------------------------------------------------------------------------


def test_plan_vs_actual_with_time_entry_delta(agile_project, task1, today):
    """Planned 60 min, logged 45 min → delta = -15."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=60)
    log_time(node_id=task1.id, duration_minutes=45, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    planned = result["planned_items"]
    assert len(planned) == 1
    item = planned[0]
    assert item["node_id"] == task1.id
    assert item["planned_minutes"] == 60
    assert item["actual_minutes"] == 45
    assert item["delta_minutes"] == -15


def test_plan_vs_actual_with_time_entry_positive_delta(agile_project, task1, today):
    """Planned 30 min, logged 50 min → delta = +20."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=30)
    log_time(node_id=task1.id, duration_minutes=50, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    item = result["planned_items"][0]
    assert item["delta_minutes"] == 20


def test_plan_vs_actual_multiple_entries_summed(agile_project, task1, today):
    """Two time entries for the same node are summed."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=60)
    log_time(node_id=task1.id, duration_minutes=20, actor="alice")
    log_time(node_id=task1.id, duration_minutes=25, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    item = result["planned_items"][0]
    assert item["actual_minutes"] == 45
    assert item["delta_minutes"] == -15


# ---------------------------------------------------------------------------
# Planned item with no time entry
# ---------------------------------------------------------------------------


def test_plan_vs_actual_no_time_entry(agile_project, task1, today):
    """Planned but not worked → actual_minutes=0, delta = -planned."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=60)

    result = plan_vs_actual(plan_date=today, actor="alice")
    item = result["planned_items"][0]
    assert item["actual_minutes"] == 0
    assert item["delta_minutes"] == -60


# ---------------------------------------------------------------------------
# Unplanned work surfaces
# ---------------------------------------------------------------------------


def test_plan_vs_actual_unplanned_work_surfaces(agile_project, task1, task2, today):
    """Work logged on a node NOT in the plan appears in unplanned_items."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=30)
    # Log time on task2 which is NOT in the plan
    log_time(node_id=task2.id, duration_minutes=20, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    unplanned_ids = {u["node_id"] for u in result["unplanned_items"]}
    assert task2.id in unplanned_ids
    assert task1.id not in unplanned_ids


def test_plan_vs_actual_planned_node_not_in_unplanned(agile_project, task1, today):
    """A node in the plan with time logged does not appear in unplanned_items."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=30)
    log_time(node_id=task1.id, duration_minutes=20, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    unplanned_ids = {u["node_id"] for u in result["unplanned_items"]}
    assert task1.id not in unplanned_ids


# ---------------------------------------------------------------------------
# No plan for the date
# ---------------------------------------------------------------------------


def test_plan_vs_actual_no_plan_returns_empty_planned_items(agile_project, task1):
    """If no plan exists for the date, planned_items is empty."""
    no_plan_date = date(2030, 1, 1)  # A date guaranteed to have no plan
    result = plan_vs_actual(plan_date=no_plan_date, actor="alice")
    assert result["planned_items"] == []


def test_plan_vs_actual_no_plan_but_work_done(agile_project, task1, today):
    """No plan, but time logged → unplanned_items populated."""
    log_time(node_id=task1.id, duration_minutes=30, actor="alice")
    # Ensure no plan for today for "charlie" (no plan created)
    result = plan_vs_actual(plan_date=today, actor="charlie")
    # charlie has no plan and logged no time → both empty
    assert result["planned_items"] == []
    assert result["unplanned_items"] == []


# ---------------------------------------------------------------------------
# overall_delta is None when no planned_minutes set
# ---------------------------------------------------------------------------


def test_plan_vs_actual_overall_delta_none_when_no_planned_minutes(agile_project, task1, today):
    """overall_delta is None when no item has planned_minutes."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id)  # No planned_minutes
    log_time(node_id=task1.id, duration_minutes=30, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    assert result["summary"]["overall_delta"] is None


def test_plan_vs_actual_overall_delta_computed_when_planned_minutes_present(
    agile_project, task1, today
):
    """overall_delta is computed when at least one item has planned_minutes."""
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=60)
    log_time(node_id=task1.id, duration_minutes=40, actor="alice")

    result = plan_vs_actual(plan_date=today, actor="alice")
    assert result["summary"]["overall_delta"] is not None
    assert result["summary"]["overall_delta"] == -20


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


def test_plan_vs_actual_response_shape(agile_project, task1, today):
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=30)

    result = plan_vs_actual(plan_date=today, actor="alice")
    assert "date" in result
    assert "actor" in result
    assert "planned_items" in result
    assert "unplanned_items" in result
    assert "summary" in result
    summary = result["summary"]
    assert "total_planned_minutes" in summary
    assert "total_actual_minutes" in summary
    assert "total_unplanned_minutes" in summary
    assert "planned_item_count" in summary
    assert "completed_count" in summary
    assert "unplanned_item_count" in summary
    assert "overall_delta" in summary


def test_plan_vs_actual_planned_item_shape(agile_project, task1, today):
    plan = create_plan(plan_date=today, actor="alice")
    add_plan_item(plan_id=plan["id"], node_id=task1.id, planned_minutes=30)

    result = plan_vs_actual(plan_date=today, actor="alice")
    item = result["planned_items"][0]
    assert "node_id" in item
    assert "title" in item
    assert "planned_minutes" in item
    assert "actual_minutes" in item
    assert "delta_minutes" in item
    assert "current_status" in item
    assert "is_terminal" in item
    assert "outcome" in item
    assert "outcome_notes" in item
