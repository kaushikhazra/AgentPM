"""Unit tests for Plan CRUD operations in core/planning.py."""

from datetime import date, timedelta

import pytest

from taskyn.core import create_company, create_project
from taskyn.db.enums import Methodology
from taskyn.core.planning import (
    UNSET,
    create_plan,
    delete_plan,
    get_plan,
    list_plans,
    update_plan,
)
from taskyn.db.connection import execute, commit
from taskyn.exceptions import NotFoundError, ValidationError
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


@pytest.fixture
def non_plannable_node(agile_project):
    return create_node(agile_project.id, node_type="story", title="A Story")


# ---------------------------------------------------------------------------
# create_plan
# ---------------------------------------------------------------------------


def test_create_plan_no_items(agile_project):
    plan = create_plan(plan_date=date(2026, 5, 1), actor="alice")
    assert plan["id"] is not None
    assert plan["date"] == date(2026, 5, 1)
    assert plan["actor"] == "alice"
    assert plan["status"] == "active"
    assert plan["notes"] is None
    assert plan["items"] == []


def test_create_plan_with_notes(agile_project):
    plan = create_plan(plan_date=date(2026, 5, 2), actor="alice", notes="Focus day")
    assert plan["notes"] == "Focus day"


def test_create_plan_with_items(agile_project, plannable_task):
    task2 = create_node(agile_project.id, node_type="task", title="Task 2")
    plan = create_plan(
        plan_date=date(2026, 5, 3),
        actor="alice",
        items=[
            {"node_id": plannable_task.id, "planned_minutes": 60},
            {"node_id": task2.id, "planned_minutes": 30},
        ],
    )
    assert len(plan["items"]) == 2
    # Items should be 1-indexed by list position
    orders = [item["display_order"] for item in plan["items"]]
    assert orders == [1, 2]
    # planned_minutes carried through
    assert plan["items"][0]["planned_minutes"] == 60
    assert plan["items"][1]["planned_minutes"] == 30


def test_create_plan_items_explicit_display_order(agile_project, plannable_task):
    task2 = create_node(agile_project.id, node_type="task", title="Task 2")
    plan = create_plan(
        plan_date=date(2026, 5, 4),
        actor="alice",
        items=[
            {"node_id": plannable_task.id, "display_order": 5},
            {"node_id": task2.id, "display_order": 1},
        ],
    )
    # Explicit display_order must be respected
    orders = sorted([item["display_order"] for item in plan["items"]])
    assert orders == [1, 5]


def test_create_plan_duplicate_raises(agile_project):
    create_plan(plan_date=date(2026, 5, 5), actor="alice")
    with pytest.raises(ValidationError, match="already exists"):
        create_plan(plan_date=date(2026, 5, 5), actor="alice")


def test_create_plan_different_actors_same_date(agile_project):
    """Two different actors can have plans on the same date."""
    p1 = create_plan(plan_date=date(2026, 5, 6), actor="alice")
    p2 = create_plan(plan_date=date(2026, 5, 6), actor="bob")
    assert p1["id"] != p2["id"]


def test_create_plan_non_plannable_item_raises(agile_project, non_plannable_node):
    with pytest.raises(ValidationError, match="not plannable"):
        create_plan(
            plan_date=date(2026, 5, 7),
            actor="alice",
            items=[{"node_id": non_plannable_node.id}],
        )


# ---------------------------------------------------------------------------
# get_plan
# ---------------------------------------------------------------------------


def test_get_plan_by_id(agile_project):
    created = create_plan(plan_date=date(2026, 5, 10), actor="alice")
    retrieved = get_plan(plan_id=created["id"])
    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["date"] == date(2026, 5, 10)


def test_get_plan_by_date_and_actor(agile_project):
    create_plan(plan_date=date(2026, 5, 11), actor="alice")
    retrieved = get_plan(plan_date=date(2026, 5, 11), actor="alice")
    assert retrieved is not None
    assert retrieved["actor"] == "alice"


def test_get_plan_today_default_when_actor_only(agile_project):
    """When only actor is given, looks up today's plan."""
    from taskyn.core.planning import _today
    today = _today()
    create_plan(plan_date=today, actor="alice")
    retrieved = get_plan(actor="alice")
    assert retrieved is not None
    assert retrieved["date"] == today


def test_get_plan_not_found_returns_none(agile_project):
    result = get_plan(plan_id="nonexistent-plan-id")
    assert result is None


def test_get_plan_no_args_returns_none(agile_project):
    result = get_plan()
    assert result is None


def test_get_plan_items_enriched_with_node_data(agile_project, plannable_task):
    plan = create_plan(
        plan_date=date(2026, 5, 12),
        actor="alice",
        items=[{"node_id": plannable_task.id}],
    )
    retrieved = get_plan(plan_id=plan["id"])
    assert len(retrieved["items"]) == 1
    item = retrieved["items"][0]
    assert item["node_id"] == plannable_task.id
    assert item["node_title"] == plannable_task.title
    assert item["node_deleted"] is False


def test_get_plan_deleted_node_returns_node_deleted_true(agile_project, plannable_task):
    """When a node is deleted after being added to a plan, node_deleted=True."""
    plan = create_plan(
        plan_date=date(2026, 5, 13),
        actor="alice",
        items=[{"node_id": plannable_task.id}],
    )
    # Delete the node directly via SQL (simulating ON DELETE SET NULL)
    execute(
        "UPDATE plan_items SET node_id = NULL WHERE plan_id = ?",
        (plan["id"],),
    )
    commit()

    retrieved = get_plan(plan_id=plan["id"])
    assert len(retrieved["items"]) == 1
    item = retrieved["items"][0]
    assert item["node_deleted"] is True
    assert item["node_id"] is None
    assert item["node_title"] is None
    assert item["node_status"] is None
    assert item["node_type"] is None
    assert item["project_id"] is None
    assert item["project_name"] is None


def test_get_plan_items_ordered_by_display_order(agile_project):
    t1 = create_node(agile_project.id, node_type="task", title="First")
    t2 = create_node(agile_project.id, node_type="task", title="Second")
    t3 = create_node(agile_project.id, node_type="task", title="Third")
    plan = create_plan(
        plan_date=date(2026, 5, 14),
        actor="alice",
        items=[{"node_id": t1.id}, {"node_id": t2.id}, {"node_id": t3.id}],
    )
    retrieved = get_plan(plan_id=plan["id"])
    orders = [item["display_order"] for item in retrieved["items"]]
    assert orders == sorted(orders)


# ---------------------------------------------------------------------------
# update_plan
# ---------------------------------------------------------------------------


def test_update_plan_notes(agile_project):
    plan = create_plan(plan_date=date(2026, 5, 20), actor="alice")
    updated = update_plan(plan_id=plan["id"], notes="New notes")
    assert updated["notes"] == "New notes"


def test_update_plan_clear_notes_with_none(agile_project):
    plan = create_plan(plan_date=date(2026, 5, 21), actor="alice", notes="Old notes")
    updated = update_plan(plan_id=plan["id"], notes=None)
    assert updated["notes"] is None


def test_update_plan_unset_leaves_notes_unchanged(agile_project):
    plan = create_plan(plan_date=date(2026, 5, 22), actor="alice", notes="Keep me")
    updated = update_plan(plan_id=plan["id"], notes=UNSET)
    assert updated["notes"] == "Keep me"


def test_update_plan_complete_with_pending_items_raises(agile_project, plannable_task):
    """Completing a plan that still has pending items raises ValidationError."""
    plan = create_plan(
        plan_date=date(2026, 5, 23),
        actor="alice",
        items=[{"node_id": plannable_task.id}],
    )
    # Default outcome is "pending" — so completing should fail
    with pytest.raises(ValidationError, match="pending"):
        update_plan(plan_id=plan["id"], status="completed")


def test_update_plan_complete_with_no_items_succeeds(agile_project):
    """Completing a plan with no items (nothing pending) succeeds."""
    plan = create_plan(plan_date=date(2026, 5, 24), actor="alice")
    updated = update_plan(plan_id=plan["id"], status="completed")
    assert updated["status"] == "completed"


def test_update_plan_complete_when_all_items_resolved(agile_project, plannable_task):
    """Completing a plan succeeds when all items have non-pending outcomes."""
    from taskyn.core.planning import update_plan_item
    plan = create_plan(
        plan_date=date(2026, 5, 25),
        actor="alice",
        items=[{"node_id": plannable_task.id}],
    )
    item_id = plan["items"][0]["id"]
    update_plan_item(item_id=item_id, outcome="completed")
    updated = update_plan(plan_id=plan["id"], status="completed")
    assert updated["status"] == "completed"


def test_update_plan_not_found_raises(agile_project):
    with pytest.raises(NotFoundError):
        update_plan(plan_id="nonexistent")


def test_update_plan_no_fields_is_noop(agile_project):
    """Calling update_plan with all UNSET fields returns current plan unchanged."""
    plan = create_plan(plan_date=date(2026, 5, 26), actor="alice", notes="Stay")
    result = update_plan(plan_id=plan["id"])
    assert result["notes"] == "Stay"
    assert result["status"] == "active"


# ---------------------------------------------------------------------------
# delete_plan
# ---------------------------------------------------------------------------


def test_delete_plan_returns_true(agile_project):
    plan = create_plan(plan_date=date(2026, 6, 1), actor="alice")
    result = delete_plan(plan_id=plan["id"])
    assert result is True


def test_delete_plan_removes_it(agile_project):
    plan = create_plan(plan_date=date(2026, 6, 2), actor="alice")
    delete_plan(plan_id=plan["id"])
    assert get_plan(plan_id=plan["id"]) is None


def test_delete_plan_cascades_items(agile_project, plannable_task):
    """Deleting a plan removes its items via CASCADE."""
    from taskyn.db.connection import fetchall
    plan = create_plan(
        plan_date=date(2026, 6, 3),
        actor="alice",
        items=[{"node_id": plannable_task.id}],
    )
    plan_id = plan["id"]
    item_id = plan["items"][0]["id"]

    delete_plan(plan_id=plan_id)

    rows = fetchall("SELECT id FROM plan_items WHERE id = ?", (item_id,))
    assert rows == []


def test_delete_plan_missing_returns_false(agile_project):
    result = delete_plan(plan_id="does-not-exist")
    assert result is False


# ---------------------------------------------------------------------------
# list_plans
# ---------------------------------------------------------------------------


@pytest.fixture
def multi_plans(agile_project):
    """Create several plans spanning different dates, actors, and statuses."""
    from taskyn.core.planning import update_plan_item
    p1 = create_plan(plan_date=date(2026, 7, 1), actor="alice")
    p2 = create_plan(plan_date=date(2026, 7, 2), actor="alice")
    p3 = create_plan(plan_date=date(2026, 7, 3), actor="bob")
    p4 = create_plan(plan_date=date(2026, 7, 4), actor="alice")
    # Complete p4 (no items so it can be completed)
    update_plan(plan_id=p4["id"], status="completed")
    return {"alice1": p1, "alice2": p2, "bob": p3, "completed": p4}


def test_list_plans_no_filter(multi_plans):
    plans = list_plans()
    assert len(plans) >= 4


def test_list_plans_actor_filter(multi_plans):
    plans = list_plans(actor="alice")
    actors = {p.actor for p in plans}
    assert actors == {"alice"}
    assert len(plans) == 3


def test_list_plans_date_from(multi_plans):
    plans = list_plans(actor="alice", date_from=date(2026, 7, 2))
    dates = {p.date for p in plans}
    assert date(2026, 7, 1) not in dates
    assert date(2026, 7, 2) in dates


def test_list_plans_date_to(multi_plans):
    plans = list_plans(actor="alice", date_to=date(2026, 7, 2))
    dates = {p.date for p in plans}
    assert date(2026, 7, 4) not in dates
    assert date(2026, 7, 1) in dates
    assert date(2026, 7, 2) in dates


def test_list_plans_date_range(multi_plans):
    plans = list_plans(date_from=date(2026, 7, 2), date_to=date(2026, 7, 3))
    dates = {p.date for p in plans}
    assert date(2026, 7, 1) not in dates
    assert date(2026, 7, 4) not in dates
    assert date(2026, 7, 2) in dates
    assert date(2026, 7, 3) in dates


def test_list_plans_status_filter(multi_plans):
    active = list_plans(status="active")
    completed = list_plans(status="completed")
    assert all(p.status == "active" for p in active)
    assert all(p.status == "completed" for p in completed)
    assert len(completed) >= 1


def test_list_plans_ordered_by_date_desc(multi_plans):
    plans = list_plans(actor="alice")
    dates = [p.date for p in plans]
    assert dates == sorted(dates, reverse=True)


def test_list_plans_limit(multi_plans):
    plans = list_plans(limit=2)
    assert len(plans) <= 2


def test_list_plans_offset_pagination(multi_plans):
    all_plans = list_plans(actor="alice")
    page1 = list_plans(actor="alice", limit=2, offset=0)
    page2 = list_plans(actor="alice", limit=2, offset=2)
    all_ids = [p.id for p in all_plans]
    page1_ids = [p.id for p in page1]
    page2_ids = [p.id for p in page2]
    # Combined pages should cover all plans
    assert set(page1_ids + page2_ids) == set(all_ids)
    # Pages should not overlap
    assert not set(page1_ids) & set(page2_ids)


# ---------------------------------------------------------------------------
# Bug-fix regression tests (B1 + B2)
# ---------------------------------------------------------------------------


def test_create_plan_inline_negative_planned_minutes_raises(agile_project, plannable_task):
    """B1: negative planned_minutes in inline items must raise ValidationError."""
    with pytest.raises(ValidationError, match="planned_minutes must be >= 0"):
        create_plan(
            plan_date=date(2026, 12, 1),
            actor="alice",
            items=[{"node_id": plannable_task.id, "planned_minutes": -10}],
        )


def test_create_plan_inline_zero_display_order_raises(agile_project, plannable_task):
    """B1: display_order < 1 in inline items must raise ValidationError."""
    with pytest.raises(ValidationError, match="display_order must be >= 1"):
        create_plan(
            plan_date=date(2026, 12, 2),
            actor="alice",
            items=[{"node_id": plannable_task.id, "display_order": 0}],
        )


def test_create_plan_inline_negative_display_order_raises(agile_project, plannable_task):
    """B1: negative display_order in inline items must raise ValidationError."""
    with pytest.raises(ValidationError, match="display_order must be >= 1"):
        create_plan(
            plan_date=date(2026, 12, 3),
            actor="alice",
            items=[{"node_id": plannable_task.id, "display_order": -5}],
        )


def test_create_plan_inline_zero_planned_minutes_allowed(agile_project, plannable_task):
    """B1: planned_minutes=0 is valid (>= 0 boundary)."""
    plan = create_plan(
        plan_date=date(2026, 12, 4),
        actor="alice",
        items=[{"node_id": plannable_task.id, "planned_minutes": 0}],
    )
    assert plan["items"][0]["planned_minutes"] == 0


def test_create_plan_inline_duplicate_node_id_raises(agile_project, plannable_task):
    """B2: duplicate node_id in inline items must raise a friendly ValidationError."""
    with pytest.raises(ValidationError, match="Duplicate node_id"):
        create_plan(
            plan_date=date(2026, 12, 5),
            actor="alice",
            items=[
                {"node_id": plannable_task.id, "planned_minutes": 30},
                {"node_id": plannable_task.id, "planned_minutes": 15},
            ],
        )
