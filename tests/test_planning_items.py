"""Unit tests for plan item operations in core/planning.py."""

from datetime import date

import pytest

from taskyn.core import create_company, create_project
from taskyn.db.enums import Methodology
from taskyn.core.planning import (
    UNSET,
    add_plan_item,
    create_plan,
    get_plan,
    remove_plan_item,
    reorder_plan_item,
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


@pytest.fixture
def empty_plan(agile_project):
    return create_plan(plan_date=date(2026, 8, 1), actor="alice")


def make_task(project, n=1):
    return create_node(project.id, node_type="task", title=f"Task {n}")


# ---------------------------------------------------------------------------
# add_plan_item
# ---------------------------------------------------------------------------


def test_add_plan_item_appends_to_end(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    t2 = make_task(agile_project, 2)
    add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    item2 = add_plan_item(plan_id=empty_plan["id"], node_id=t2.id)
    assert item2.display_order == 2


def test_add_plan_item_at_position_shifts_others(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    t2 = make_task(agile_project, 2)
    t3 = make_task(agile_project, 3)
    add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    add_plan_item(plan_id=empty_plan["id"], node_id=t2.id)
    # Insert t3 at position 1 — t1 and t2 should shift down
    add_plan_item(plan_id=empty_plan["id"], node_id=t3.id, position=1)

    plan = get_plan(plan_id=empty_plan["id"])
    order_map = {item["node_id"]: item["display_order"] for item in plan["items"]}
    assert order_map[t3.id] == 1
    assert order_map[t1.id] == 2
    assert order_map[t2.id] == 3


def test_add_plan_item_duplicate_node_raises(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    with pytest.raises(ValidationError, match="already in plan"):
        add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)


def test_add_plan_item_negative_minutes_raises(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    with pytest.raises(ValidationError, match="planned_minutes"):
        add_plan_item(plan_id=empty_plan["id"], node_id=t1.id, planned_minutes=-1)


def test_add_plan_item_zero_minutes_ok(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    # 0 is a valid value (>= 0)
    item = add_plan_item(plan_id=empty_plan["id"], node_id=t1.id, planned_minutes=0)
    assert item.planned_minutes == 0


def test_add_plan_item_position_zero_raises(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    with pytest.raises(ValidationError, match="position"):
        add_plan_item(plan_id=empty_plan["id"], node_id=t1.id, position=0)


def test_add_plan_item_position_negative_raises(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    with pytest.raises(ValidationError, match="position"):
        add_plan_item(plan_id=empty_plan["id"], node_id=t1.id, position=-1)


def test_add_plan_item_non_plannable_raises(agile_project, empty_plan):
    story = create_node(agile_project.id, node_type="story", title="A Story")
    with pytest.raises(ValidationError, match="not plannable"):
        add_plan_item(plan_id=empty_plan["id"], node_id=story.id)


def test_add_plan_item_plan_not_found_raises(agile_project):
    t1 = make_task(agile_project, 1)
    with pytest.raises(NotFoundError):
        add_plan_item(plan_id="nonexistent-plan", node_id=t1.id)


def test_add_plan_item_terminal_status_node_allowed(agile_project, empty_plan):
    """Terminal-status nodes (done/cancelled) are intentionally allowed in plans."""
    from taskyn.graph import update_node
    t1 = make_task(agile_project, 1)
    # Transition task to done: todo → in_progress → done
    update_node(t1.id, status="in_progress")
    update_node(t1.id, status="done")
    # Should NOT raise
    item = add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    assert item.node_id == t1.id


# ---------------------------------------------------------------------------
# remove_plan_item
# ---------------------------------------------------------------------------


def test_remove_plan_item_returns_true(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    item = add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    result = remove_plan_item(item_id=item.id)
    assert result is True


def test_remove_plan_item_actually_removes(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    item = add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    remove_plan_item(item_id=item.id)
    plan = get_plan(plan_id=empty_plan["id"])
    assert len(plan["items"]) == 0


def test_remove_plan_item_recompacts_display_order(agile_project, empty_plan):
    t1 = make_task(agile_project, 1)
    t2 = make_task(agile_project, 2)
    t3 = make_task(agile_project, 3)
    i1 = add_plan_item(plan_id=empty_plan["id"], node_id=t1.id)
    i2 = add_plan_item(plan_id=empty_plan["id"], node_id=t2.id)
    i3 = add_plan_item(plan_id=empty_plan["id"], node_id=t3.id)
    # Remove the middle item
    remove_plan_item(item_id=i2.id)
    plan = get_plan(plan_id=empty_plan["id"])
    orders = [item["display_order"] for item in plan["items"]]
    assert orders == [1, 2]  # Gaps removed; no longer [1, 3]


def test_remove_plan_item_missing_returns_false(agile_project):
    result = remove_plan_item(item_id="does-not-exist")
    assert result is False


# ---------------------------------------------------------------------------
# update_plan_item
# ---------------------------------------------------------------------------


@pytest.fixture
def plan_with_one_task(agile_project):
    t = make_task(agile_project, 1)
    plan = create_plan(plan_date=date(2026, 8, 10), actor="alice")
    item = add_plan_item(plan_id=plan["id"], node_id=t.id, planned_minutes=60)
    return {"plan": plan, "item": item, "task": t}


def test_update_plan_item_negative_minutes_raises(plan_with_one_task):
    item = plan_with_one_task["item"]
    with pytest.raises(ValidationError, match="planned_minutes"):
        update_plan_item(item_id=item.id, planned_minutes=-1)


def test_update_plan_item_zero_minutes_ok(plan_with_one_task):
    item = plan_with_one_task["item"]
    updated = update_plan_item(item_id=item.id, planned_minutes=0)
    assert updated.planned_minutes == 0


def test_update_plan_item_invalid_outcome_raises(plan_with_one_task):
    item = plan_with_one_task["item"]
    with pytest.raises(ValidationError, match="Invalid outcome"):
        update_plan_item(item_id=item.id, outcome="not_a_real_outcome")


def test_update_plan_item_valid_outcome(plan_with_one_task):
    item = plan_with_one_task["item"]
    updated = update_plan_item(item_id=item.id, outcome="partial")
    assert updated.outcome == "partial"


def test_update_plan_item_none_clears_planned_minutes(plan_with_one_task):
    item = plan_with_one_task["item"]
    updated = update_plan_item(item_id=item.id, planned_minutes=None)
    assert updated.planned_minutes is None


def test_update_plan_item_none_clears_outcome_notes(plan_with_one_task):
    item = plan_with_one_task["item"]
    # First set notes
    update_plan_item(item_id=item.id, outcome_notes="Some notes")
    # Then clear
    updated = update_plan_item(item_id=item.id, outcome_notes=None)
    assert updated.outcome_notes is None


def test_update_plan_item_unset_leaves_field_unchanged(plan_with_one_task):
    item = plan_with_one_task["item"]
    # planned_minutes=UNSET → should remain 60
    updated = update_plan_item(item_id=item.id, planned_minutes=UNSET)
    assert updated.planned_minutes == 60


def test_update_plan_item_not_found_raises(agile_project):
    with pytest.raises(NotFoundError):
        update_plan_item(item_id="does-not-exist")


# ---------------------------------------------------------------------------
# reorder_plan_item — exhaustive W3 tests
# ---------------------------------------------------------------------------


def _make_plan_with_n_tasks(project, n: int, plan_date: date) -> tuple:
    """Create a plan with n task items. Return (plan_dict, [item_id, ...])."""
    tasks = [make_task(project, i + 1) for i in range(n)]
    plan = create_plan(plan_date=plan_date, actor="alice")
    items = [add_plan_item(plan_id=plan["id"], node_id=t.id) for t in tasks]
    return plan, items


def _current_order(plan_id: str) -> list[str]:
    """Return node_id list ordered by display_order."""
    plan = get_plan(plan_id=plan_id)
    return [item["node_id"] for item in plan["items"]]


def test_reorder_same_position_is_noop(agile_project):
    """Moving item to its current position changes nothing."""
    plan, items = _make_plan_with_n_tasks(agile_project, 3, date(2026, 9, 1))
    original_order = _current_order(plan["id"])
    reorder_plan_item(item_id=items[0].id, new_position=1)  # already at 1
    assert _current_order(plan["id"]) == original_order


def test_reorder_move_to_first(agile_project):
    """Move item at position 3 to position 1."""
    plan, items = _make_plan_with_n_tasks(agile_project, 3, date(2026, 9, 2))
    reorder_plan_item(item_id=items[2].id, new_position=1)
    order = _current_order(plan["id"])
    assert order[0] == items[2].node_id
    assert order[1] == items[0].node_id
    assert order[2] == items[1].node_id


def test_reorder_move_to_last(agile_project):
    """Move item at position 1 to position 3 (last)."""
    plan, items = _make_plan_with_n_tasks(agile_project, 3, date(2026, 9, 3))
    reorder_plan_item(item_id=items[0].id, new_position=3)
    order = _current_order(plan["id"])
    assert order[0] == items[1].node_id
    assert order[1] == items[2].node_id
    assert order[2] == items[0].node_id


def test_reorder_first_to_last(agile_project):
    """Move first item to last position in a 4-item list."""
    plan, items = _make_plan_with_n_tasks(agile_project, 4, date(2026, 9, 4))
    reorder_plan_item(item_id=items[0].id, new_position=4)
    order = _current_order(plan["id"])
    assert order[3] == items[0].node_id


def test_reorder_last_to_first(agile_project):
    """Move last item to first position in a 4-item list."""
    plan, items = _make_plan_with_n_tasks(agile_project, 4, date(2026, 9, 5))
    reorder_plan_item(item_id=items[3].id, new_position=1)
    order = _current_order(plan["id"])
    assert order[0] == items[3].node_id


def test_reorder_in_2_item_list_swap(agile_project):
    """In a 2-item list, moving item 1 to position 2 swaps them."""
    plan, items = _make_plan_with_n_tasks(agile_project, 2, date(2026, 9, 6))
    reorder_plan_item(item_id=items[0].id, new_position=2)
    order = _current_order(plan["id"])
    assert order[0] == items[1].node_id
    assert order[1] == items[0].node_id


def test_reorder_in_1_item_list(agile_project):
    """A single-item plan: reorder to position 1 is a no-op."""
    plan, items = _make_plan_with_n_tasks(agile_project, 1, date(2026, 9, 7))
    result = reorder_plan_item(item_id=items[0].id, new_position=1)
    assert result.display_order == 1


def test_reorder_out_of_bounds_raises(agile_project):
    """new_position > item count raises ValidationError."""
    plan, items = _make_plan_with_n_tasks(agile_project, 3, date(2026, 9, 8))
    with pytest.raises(ValidationError, match="exceeds item count"):
        reorder_plan_item(item_id=items[0].id, new_position=4)


def test_reorder_position_less_than_1_raises(agile_project):
    """new_position < 1 raises ValidationError."""
    plan, items = _make_plan_with_n_tasks(agile_project, 3, date(2026, 9, 9))
    with pytest.raises(ValidationError, match="new_position must be"):
        reorder_plan_item(item_id=items[0].id, new_position=0)


def test_reorder_item_not_found_raises(agile_project):
    with pytest.raises(NotFoundError):
        reorder_plan_item(item_id="does-not-exist", new_position=1)


def test_reorder_middle_forward(agile_project):
    """Move item at position 2 to position 4 in a 5-item list."""
    plan, items = _make_plan_with_n_tasks(agile_project, 5, date(2026, 9, 10))
    target = items[1]  # position 2 (0-indexed)
    reorder_plan_item(item_id=target.id, new_position=4)
    order = _current_order(plan["id"])
    assert order[3] == target.node_id


def test_reorder_middle_backward(agile_project):
    """Move item at position 4 to position 2 in a 5-item list."""
    plan, items = _make_plan_with_n_tasks(agile_project, 5, date(2026, 9, 11))
    target = items[3]  # position 4 (0-indexed)
    reorder_plan_item(item_id=target.id, new_position=2)
    order = _current_order(plan["id"])
    assert order[1] == target.node_id


def test_reorder_result_has_new_display_order(agile_project):
    """reorder_plan_item returns the updated PlanItem with new display_order."""
    plan, items = _make_plan_with_n_tasks(agile_project, 3, date(2026, 9, 12))
    result = reorder_plan_item(item_id=items[2].id, new_position=1)
    assert result.display_order == 1


def test_reorder_no_duplicate_orders(agile_project):
    """After any reorder, all display_orders in the plan are unique and contiguous."""
    plan, items = _make_plan_with_n_tasks(agile_project, 4, date(2026, 9, 13))
    reorder_plan_item(item_id=items[3].id, new_position=1)
    reorder_plan_item(item_id=items[0].id, new_position=3)
    plan_data = get_plan(plan_id=plan["id"])
    orders = sorted([item["display_order"] for item in plan_data["items"]])
    assert orders == [1, 2, 3, 4]
