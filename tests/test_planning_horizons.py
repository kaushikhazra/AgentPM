"""Unit tests for horizon view functions (get_weekly_plan, get_monthly_plan)."""

import calendar
from datetime import date, timedelta

import pytest

from taskyn.core import create_company, create_project
from taskyn.db.enums import Methodology
from taskyn.core.planning import (
    add_plan_item,
    create_plan,
    get_monthly_plan,
    get_weekly_plan,
)
from taskyn.db.connection import execute, commit
from taskyn.exceptions import ValidationError
from taskyn.graph import create_node


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agile_project(temp_db):
    company = create_company("Test Co")
    return create_project(company.id, "Agile Project", Methodology.CLASSIC_AGILE)


@pytest.fixture
def plannable_task(agile_project):
    return create_node(agile_project.id, node_type="task", title="A Task")


# ---------------------------------------------------------------------------
# get_weekly_plan — snapping
# ---------------------------------------------------------------------------


def test_weekly_plan_wednesday_snaps_to_monday(agile_project):
    """Any day in the week should snap to the same Monday."""
    wednesday = date(2026, 4, 8)  # a Wednesday
    monday = date(2026, 4, 6)     # the Monday of that week
    result = get_weekly_plan(week_start_date=wednesday)
    assert result["week_start"] == monday
    assert result["week_end"] == monday + timedelta(days=6)


def test_weekly_plan_monday_input_unchanged(agile_project):
    monday = date(2026, 4, 6)
    result = get_weekly_plan(week_start_date=monday)
    assert result["week_start"] == monday


def test_weekly_plan_sunday_snaps_to_its_monday(agile_project):
    sunday = date(2026, 4, 12)  # Sunday of the same week as April 6
    monday = date(2026, 4, 6)
    result = get_weekly_plan(week_start_date=sunday)
    assert result["week_start"] == monday


# ---------------------------------------------------------------------------
# get_weekly_plan — structure
# ---------------------------------------------------------------------------


def test_weekly_plan_returns_7_day_slots(agile_project):
    result = get_weekly_plan(week_start_date=date(2026, 4, 6))
    assert len(result["days"]) == 7


def test_weekly_plan_day_slots_are_lists(agile_project):
    """Each slot in days must be a list (not None, not a dict)."""
    result = get_weekly_plan(week_start_date=date(2026, 4, 6))
    for slot in result["days"]:
        assert isinstance(slot, list)


def test_weekly_plan_empty_week_all_empty_lists(agile_project):
    """A week with no plans returns 7 empty lists."""
    result = get_weekly_plan(week_start_date=date(2026, 4, 6))
    assert all(slot == [] for slot in result["days"])


def test_weekly_plan_empty_week_zero_summary(agile_project):
    result = get_weekly_plan(week_start_date=date(2026, 4, 6))
    s = result["summary"]
    assert s["total_planned_items"] == 0
    assert s["total_planned_minutes"] == 0
    assert s["actual_minutes"] == 0


def test_weekly_plan_summary_keys_present(agile_project):
    result = get_weekly_plan(week_start_date=date(2026, 4, 6))
    assert "total_planned_items" in result["summary"]
    assert "total_planned_minutes" in result["summary"]
    assert "outcomes" in result["summary"]
    assert "actual_minutes" in result["summary"]


# ---------------------------------------------------------------------------
# get_weekly_plan — plans appear in correct day slot
# ---------------------------------------------------------------------------


def test_weekly_plan_plan_appears_in_correct_slot(agile_project):
    monday = date(2026, 4, 6)
    wednesday = date(2026, 4, 8)  # slot index 2 (0=Mon, 2=Wed)
    create_plan(plan_date=wednesday, actor="alice")
    result = get_weekly_plan(week_start_date=monday, actor="alice")
    assert result["days"][2] != []  # Wednesday slot has a plan
    assert result["days"][0] == []  # Monday slot is empty
    assert result["days"][6] == []  # Sunday slot is empty


def test_weekly_plan_two_actors_same_day_both_appear(agile_project):
    """Without an actor filter, two actors on the same day both show up in the slot."""
    monday = date(2026, 5, 4)
    tuesday = date(2026, 5, 5)  # slot index 1
    create_plan(plan_date=tuesday, actor="alice")
    create_plan(plan_date=tuesday, actor="bob")
    result = get_weekly_plan(week_start_date=monday)  # no actor filter
    tuesday_slot = result["days"][1]
    actors_in_slot = {p["actor"] for p in tuesday_slot}
    assert "alice" in actors_in_slot
    assert "bob" in actors_in_slot


def test_weekly_plan_actor_filter_excludes_others(agile_project):
    """With an actor filter, only that actor's plans appear."""
    monday = date(2026, 5, 11)
    tuesday = date(2026, 5, 12)
    create_plan(plan_date=tuesday, actor="alice")
    create_plan(plan_date=tuesday, actor="bob")
    result = get_weekly_plan(week_start_date=monday, actor="alice")
    tuesday_slot = result["days"][1]
    assert len(tuesday_slot) == 1
    assert tuesday_slot[0]["actor"] == "alice"


def test_weekly_plan_summary_counts_items_across_week(agile_project, plannable_task):
    monday = date(2026, 5, 18)
    t2 = create_node(agile_project.id, node_type="task", title="Task 2")
    p1 = create_plan(plan_date=date(2026, 5, 18), actor="alice")
    p2 = create_plan(plan_date=date(2026, 5, 19), actor="alice")
    add_plan_item(plan_id=p1["id"], node_id=plannable_task.id, planned_minutes=60)
    add_plan_item(plan_id=p2["id"], node_id=t2.id, planned_minutes=30)
    result = get_weekly_plan(week_start_date=monday, actor="alice")
    assert result["summary"]["total_planned_items"] == 2
    assert result["summary"]["total_planned_minutes"] == 90


# ---------------------------------------------------------------------------
# get_monthly_plan — structure
# ---------------------------------------------------------------------------


def test_monthly_plan_days_in_month_correct(agile_project):
    """days_in_month must match calendar.monthrange."""
    for year, month in [(2026, 1), (2026, 2), (2026, 4), (2026, 12)]:
        _, expected = calendar.monthrange(year, month)
        result = get_monthly_plan(year=year, month=month)
        assert result["days_in_month"] == expected


def test_monthly_plan_february_28_in_non_leap(agile_project):
    _, days = calendar.monthrange(2025, 2)
    result = get_monthly_plan(year=2025, month=2)
    assert result["days_in_month"] == days  # 28


def test_monthly_plan_february_29_in_leap(agile_project):
    _, days = calendar.monthrange(2024, 2)
    result = get_monthly_plan(year=2024, month=2)
    assert result["days_in_month"] == days  # 29


def test_monthly_plan_result_keys(agile_project):
    result = get_monthly_plan(year=2026, month=1)
    expected_keys = {
        "year", "month", "days_in_month", "days_with_plans",
        "total_planned_items", "total_planned_minutes", "outcomes",
        "actual_minutes", "per_actor", "milestones",
    }
    assert expected_keys.issubset(result.keys())


def test_monthly_plan_empty_month(agile_project):
    result = get_monthly_plan(year=2026, month=3)
    assert result["days_with_plans"] == 0
    assert result["total_planned_items"] == 0
    assert result["total_planned_minutes"] == 0
    assert result["milestones"] == []
    assert result["per_actor"] == []


# ---------------------------------------------------------------------------
# get_monthly_plan — per_actor breakdown
# ---------------------------------------------------------------------------


def test_monthly_plan_per_actor_populated_without_actor_filter(agile_project, plannable_task):
    t2 = create_node(agile_project.id, node_type="task", title="T2")
    p1 = create_plan(plan_date=date(2026, 10, 1), actor="alice")
    p2 = create_plan(plan_date=date(2026, 10, 2), actor="bob")
    add_plan_item(plan_id=p1["id"], node_id=plannable_task.id, planned_minutes=30)
    add_plan_item(plan_id=p2["id"], node_id=t2.id, planned_minutes=20)
    result = get_monthly_plan(year=2026, month=10)
    actors_in_breakdown = {entry["actor"] for entry in result["per_actor"]}
    assert "alice" in actors_in_breakdown
    assert "bob" in actors_in_breakdown


def test_monthly_plan_per_actor_empty_with_actor_filter(agile_project, plannable_task):
    create_plan(plan_date=date(2026, 10, 5), actor="alice")
    result = get_monthly_plan(year=2026, month=10, actor="alice")
    assert result["per_actor"] == []


# ---------------------------------------------------------------------------
# get_monthly_plan — milestones
# ---------------------------------------------------------------------------


def test_monthly_plan_milestones_use_completed_at_is_null(agile_project):
    """Milestone query uses completed_at IS NULL — not status = 'open'."""
    from taskyn.core import create_milestone, complete_milestone
    # Create one open and one completed milestone in the same month
    m_open = create_milestone(
        project_id=agile_project.id,
        name="Open Milestone",
        target_date=date(2026, 11, 15),
    )
    m_done = create_milestone(
        project_id=agile_project.id,
        name="Done Milestone",
        target_date=date(2026, 11, 20),
    )
    complete_milestone(milestone_id=m_done.id)

    result = get_monthly_plan(year=2026, month=11)
    milestone_ids = {m["id"] for m in result["milestones"]}
    assert m_open.id in milestone_ids
    assert m_done.id not in milestone_ids  # completed_at IS NOT NULL → excluded


def test_monthly_plan_milestones_outside_month_excluded(agile_project):
    from taskyn.core import create_milestone
    create_milestone(
        project_id=agile_project.id,
        name="In Month",
        target_date=date(2026, 12, 15),
    )
    create_milestone(
        project_id=agile_project.id,
        name="Before Month",
        target_date=date(2026, 11, 30),
    )
    create_milestone(
        project_id=agile_project.id,
        name="After Month",
        target_date=date(2027, 1, 1),
    )
    result = get_monthly_plan(year=2026, month=12)
    names = {m["name"] for m in result["milestones"]}
    assert "In Month" in names
    assert "Before Month" not in names
    assert "After Month" not in names


def test_monthly_plan_milestones_have_expected_fields(agile_project):
    from taskyn.core import create_milestone
    create_milestone(
        project_id=agile_project.id,
        name="Check Fields",
        target_date=date(2026, 12, 10),
    )
    result = get_monthly_plan(year=2026, month=12)
    assert len(result["milestones"]) >= 1
    m = result["milestones"][0]
    assert "id" in m
    assert "name" in m
    assert "project_id" in m
    assert "project_name" in m
    assert "target_date" in m
    assert "status" in m


# ---------------------------------------------------------------------------
# get_monthly_plan — counts
# ---------------------------------------------------------------------------


def test_monthly_plan_days_with_plans(agile_project):
    create_plan(plan_date=date(2026, 10, 1), actor="alice")
    create_plan(plan_date=date(2026, 10, 1), actor="bob")  # same day, different actor
    create_plan(plan_date=date(2026, 10, 3), actor="alice")
    result = get_monthly_plan(year=2026, month=10)
    # Two distinct days have plans (Oct 1 and Oct 3)
    assert result["days_with_plans"] == 2
