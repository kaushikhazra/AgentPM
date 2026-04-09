"""Unit tests for carry_over_plan in core/planning.py."""

from datetime import date

import pytest

from taskyn.core import create_company, create_project
from taskyn.db.enums import Methodology
from taskyn.core.planning import (
    add_plan_item,
    carry_over_plan,
    create_plan,
    get_plan,
    update_plan_item,
)
from taskyn.exceptions import NotFoundError, ValidationError
from taskyn.graph import create_node


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agile_project(temp_db):
    company = create_company("Test Co")
    return create_project(company.id, "Agile Project", Methodology.CLASSIC_AGILE)


def make_task(project, n=1):
    return create_node(project.id, node_type="task", title=f"Task {n}")


SOURCE_DATE = date(2026, 6, 1)
TARGET_DATE = date(2026, 6, 2)  # One day after source
PAST_TARGET = date(2026, 5, 30)  # Before source date
EQUAL_DATE = date(2026, 6, 1)   # Same as source


@pytest.fixture
def source_plan_with_tasks(agile_project):
    """Create a source plan with 3 tasks: pending, partial, and completed."""
    t1 = make_task(agile_project, 1)
    t2 = make_task(agile_project, 2)
    t3 = make_task(agile_project, 3)
    t4 = make_task(agile_project, 4)  # dropped
    plan = create_plan(plan_date=SOURCE_DATE, actor="alice")
    i1 = add_plan_item(plan_id=plan["id"], node_id=t1.id, planned_minutes=30)
    i2 = add_plan_item(plan_id=plan["id"], node_id=t2.id, planned_minutes=60)
    i3 = add_plan_item(plan_id=plan["id"], node_id=t3.id, planned_minutes=45)
    i4 = add_plan_item(plan_id=plan["id"], node_id=t4.id, planned_minutes=20)
    # Set outcomes: i1=pending (default), i2=partial, i3=completed, i4=dropped
    update_plan_item(item_id=i2.id, outcome="partial")
    update_plan_item(item_id=i3.id, outcome="completed")
    update_plan_item(item_id=i4.id, outcome="dropped")
    return {
        "plan": plan,
        "tasks": [t1, t2, t3, t4],
        "items": [i1, i2, i3, i4],
    }


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_carry_over_source_not_found_raises(temp_db):
    with pytest.raises(NotFoundError):
        carry_over_plan(source_plan_id="nonexistent", target_date=TARGET_DATE)


def test_carry_over_target_date_equal_to_source_raises(agile_project, source_plan_with_tasks):
    source_plan_id = source_plan_with_tasks["plan"]["id"]
    with pytest.raises(ValidationError, match="strictly after"):
        carry_over_plan(source_plan_id=source_plan_id, target_date=EQUAL_DATE)


def test_carry_over_target_date_before_source_raises(agile_project, source_plan_with_tasks):
    source_plan_id = source_plan_with_tasks["plan"]["id"]
    with pytest.raises(ValidationError, match="strictly after"):
        carry_over_plan(source_plan_id=source_plan_id, target_date=PAST_TARGET)


# ---------------------------------------------------------------------------
# W7: Past target date after source succeeds
# ---------------------------------------------------------------------------


def test_carry_over_past_target_after_source_succeeds(agile_project):
    """Carrying to a past date that is still after the source is allowed (W7)."""
    # Source on June 5, target on June 6 (both in the past relative to today)
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 6, 5), actor="alice")
    add_plan_item(plan_id=source["id"], node_id=t1.id)
    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 6, 6),
    )
    assert result["carried_count"] == 1


# ---------------------------------------------------------------------------
# Pending + partial items are carried
# ---------------------------------------------------------------------------


def test_carry_over_carries_pending_and_partial(agile_project, source_plan_with_tasks):
    source_plan_id = source_plan_with_tasks["plan"]["id"]
    tasks = source_plan_with_tasks["tasks"]
    result = carry_over_plan(source_plan_id=source_plan_id, target_date=TARGET_DATE)
    assert result["carried_count"] == 2
    target_plan = result["target_plan"]
    carried_node_ids = {item["node_id"] for item in target_plan["items"]}
    assert tasks[0].id in carried_node_ids   # pending → carried
    assert tasks[1].id in carried_node_ids   # partial → carried
    assert tasks[2].id not in carried_node_ids  # completed → skipped
    assert tasks[3].id not in carried_node_ids  # dropped → skipped


# ---------------------------------------------------------------------------
# Completed + dropped items skipped as already_resolved
# ---------------------------------------------------------------------------


def test_carry_over_completed_and_dropped_skipped(agile_project, source_plan_with_tasks):
    source_plan_id = source_plan_with_tasks["plan"]["id"]
    items = source_plan_with_tasks["items"]
    result = carry_over_plan(source_plan_id=source_plan_id, target_date=TARGET_DATE)
    skipped_ids = {s["item_id"] for s in result["skipped"]}
    skipped_reasons = {s["item_id"]: s["reason"] for s in result["skipped"]}
    assert items[2].id in skipped_ids  # completed
    assert items[3].id in skipped_ids  # dropped
    assert skipped_reasons[items[2].id] == "already_resolved"
    assert skipped_reasons[items[3].id] == "already_resolved"


# ---------------------------------------------------------------------------
# Node already in target skipped as already_in_target
# ---------------------------------------------------------------------------


def test_carry_over_skips_node_already_in_target(agile_project):
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 6, 10), actor="alice")
    i1 = add_plan_item(plan_id=source["id"], node_id=t1.id)

    # Pre-create target with same node
    target = create_plan(plan_date=date(2026, 6, 11), actor="alice")
    add_plan_item(plan_id=target["id"], node_id=t1.id)

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 6, 11),
    )
    skipped_reasons = {s["item_id"]: s["reason"] for s in result["skipped"]}
    assert skipped_reasons[i1.id] == "already_in_target"
    assert result["carried_count"] == 0


# ---------------------------------------------------------------------------
# Target plan created when not exists
# ---------------------------------------------------------------------------


def test_carry_over_creates_target_plan_when_not_exists(agile_project):
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 7, 1), actor="alice")
    add_plan_item(plan_id=source["id"], node_id=t1.id)

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 7, 2),
    )
    target_plan = result["target_plan"]
    assert target_plan is not None
    assert target_plan["date"] == date(2026, 7, 2)
    assert target_plan["actor"] == "alice"  # Inherits actor from source


def test_carry_over_target_plan_inherits_source_actor(agile_project):
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 7, 5), actor="bob")
    add_plan_item(plan_id=source["id"], node_id=t1.id)

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 7, 6),
    )
    assert result["target_plan"]["actor"] == "bob"


# ---------------------------------------------------------------------------
# Items appended when target plan already exists
# ---------------------------------------------------------------------------


def test_carry_over_appends_to_existing_target_plan(agile_project):
    t1 = make_task(agile_project, 1)
    t2 = make_task(agile_project, 2)
    source = create_plan(plan_date=date(2026, 7, 10), actor="alice")
    add_plan_item(plan_id=source["id"], node_id=t1.id)

    # Pre-create target with t2 already in it
    target = create_plan(plan_date=date(2026, 7, 11), actor="alice")
    add_plan_item(plan_id=target["id"], node_id=t2.id)

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 7, 11),
    )
    target_plan = result["target_plan"]
    carried_node_ids = {item["node_id"] for item in target_plan["items"]}
    # Both the pre-existing t2 and the carried t1 should be there
    assert t1.id in carried_node_ids
    assert t2.id in carried_node_ids
    assert result["carried_count"] == 1


# ---------------------------------------------------------------------------
# Source items get outcome=carried_over and carried_to_plan_id set
# ---------------------------------------------------------------------------


def test_carry_over_source_items_marked_carried_over(agile_project):
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 8, 1), actor="alice")
    item = add_plan_item(plan_id=source["id"], node_id=t1.id)

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 8, 2),
    )
    # Refresh source plan to see updated outcomes
    refreshed_source = get_plan(plan_id=source["id"])
    source_item = refreshed_source["items"][0]
    assert source_item["outcome"] == "carried_over"
    assert source_item["carried_to_plan_id"] == result["target_plan"]["id"]


def test_carry_over_carried_items_have_pending_outcome_in_target(agile_project):
    """Carried items start fresh with outcome=pending in the target plan."""
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 8, 5), actor="alice")
    i1 = add_plan_item(plan_id=source["id"], node_id=t1.id)
    update_plan_item(item_id=i1.id, outcome="partial")

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 8, 6),
    )
    target_item = result["target_plan"]["items"][0]
    assert target_item["outcome"] == "pending"


# ---------------------------------------------------------------------------
# Selective carry-over via item_ids
# ---------------------------------------------------------------------------


def test_carry_over_specific_item_ids(agile_project, source_plan_with_tasks):
    """When item_ids is provided, only those items are considered for carry-over."""
    source_plan_id = source_plan_with_tasks["plan"]["id"]
    items = source_plan_with_tasks["items"]
    # Carry only the pending item (items[0])
    result = carry_over_plan(
        source_plan_id=source_plan_id,
        target_date=date(2026, 6, 15),
        item_ids=[items[0].id],
    )
    assert result["carried_count"] == 1


def test_carry_over_specific_item_ids_completed_skipped(agile_project, source_plan_with_tasks):
    """Specifying a completed item ID marks it as already_resolved."""
    source_plan_id = source_plan_with_tasks["plan"]["id"]
    items = source_plan_with_tasks["items"]
    # items[2] is completed → should be skipped
    result = carry_over_plan(
        source_plan_id=source_plan_id,
        target_date=date(2026, 6, 20),
        item_ids=[items[2].id],
    )
    assert result["carried_count"] == 0
    assert len(result["skipped"]) == 1
    assert result["skipped"][0]["reason"] == "already_resolved"


# ---------------------------------------------------------------------------
# Return shape
# ---------------------------------------------------------------------------


def test_carry_over_return_shape(agile_project):
    t1 = make_task(agile_project, 1)
    source = create_plan(plan_date=date(2026, 9, 1), actor="alice")
    add_plan_item(plan_id=source["id"], node_id=t1.id)

    result = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 9, 2),
    )
    assert "source_plan_id" in result
    assert "target_plan" in result
    assert "carried_count" in result
    assert "skipped" in result


# ---------------------------------------------------------------------------
# Bug-fix regression test (B3)
# ---------------------------------------------------------------------------


def test_carry_over_explicit_already_carried_item_is_skipped(agile_project):
    """B3: explicit item_ids must not re-carry an item already marked carried_over."""
    t1 = make_task(agile_project, 1)
    t2 = make_task(agile_project, 2)

    source = create_plan(plan_date=date(2026, 10, 1), actor="alice")
    i1 = add_plan_item(plan_id=source["id"], node_id=t1.id)
    i2 = add_plan_item(plan_id=source["id"], node_id=t2.id)

    # First carry: carry i1 to 10-02 — it becomes carried_over
    first = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 10, 2),
        item_ids=[i1.id],
    )
    assert first["carried_count"] == 1
    first_target_plan_id = first["target_plan"]["id"]

    # Verify i1 is now carried_over in the source
    refreshed = get_plan(plan_id=source["id"])
    item_i1 = next(it for it in refreshed["items"] if it["id"] == i1.id)
    assert item_i1["outcome"] == "carried_over"
    assert item_i1["carried_to_plan_id"] == first_target_plan_id

    # Second carry: explicitly re-request i1 along with i2 — i1 must be skipped
    second = carry_over_plan(
        source_plan_id=source["id"],
        target_date=date(2026, 10, 3),
        item_ids=[i1.id, i2.id],
    )
    assert second["carried_count"] == 1, "Only i2 (pending) should be carried"
    skipped_ids = [s["item_id"] for s in second["skipped"]]
    assert i1.id in skipped_ids, "Already-carried i1 must appear in skipped"
    skipped_i1 = next(s for s in second["skipped"] if s["item_id"] == i1.id)
    assert skipped_i1["reason"] == "already_carried"

    # i1's carried_to_plan_id must still point to the FIRST target (not overwritten)
    refreshed2 = get_plan(plan_id=source["id"])
    item_i1_again = next(it for it in refreshed2["items"] if it["id"] == i1.id)
    assert item_i1_again["carried_to_plan_id"] == first_target_plan_id, (
        "carried_to_plan_id must not be overwritten by the second carry"
    )
