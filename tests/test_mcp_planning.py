"""Integration tests for MCP planning tools (Section 11 of task.md)."""

import inspect
import json
from datetime import date

import pytest
from fastmcp import Client

from taskyn.core import create_company, create_project
from taskyn.db.enums import Methodology
from taskyn.core.planning import _today
from taskyn.graph import create_node
from taskyn.mcp.server import mcp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def client(temp_db):
    """Create a FastMCP in-memory client for testing."""
    return Client(mcp)


def get_result(call_result):
    """Extract the actual result from CallToolResult."""
    if hasattr(call_result, "structured_content") and call_result.structured_content:
        return call_result.structured_content.get("result", call_result.structured_content)
    if hasattr(call_result, "data") and call_result.data is not None:
        return call_result.data
    if hasattr(call_result, "content") and call_result.content:
        for item in call_result.content:
            if hasattr(item, "text"):
                try:
                    return json.loads(item.text)
                except (json.JSONDecodeError, TypeError):
                    return item.text
    return None


@pytest.fixture
def agile_project(temp_db):
    company = create_company("MCP Test Co")
    return create_project(company.id, "MCP Agile Project", Methodology.CLASSIC_AGILE)


@pytest.fixture
def plannable_task(agile_project):
    return create_node(agile_project.id, node_type="task", title="MCP Task")


# ---------------------------------------------------------------------------
# pm_create_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_create_plan(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-01",
            "actor": "test-actor",
            "notes": "Test plan",
        }))
    assert result is not None
    assert result["date"] in ("2026-09-01", date(2026, 9, 1))
    assert result["actor"] == "test-actor"
    assert result["notes"] == "Test plan"
    assert result["status"] == "active"
    assert isinstance(result["items"], list)
    assert "id" in result


# ---------------------------------------------------------------------------
# pm_get_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_get_plan_by_id(client, agile_project):
    async with client:
        created = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-02",
            "actor": "test-actor",
        }))
        result = get_result(await client.call_tool("pm_get_plan", {
            "plan_id": created["id"],
        }))
    assert result is not None
    assert result["id"] == created["id"]


@pytest.mark.asyncio
async def test_mcp_get_plan_not_found_returns_none(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_plan", {
            "plan_id": "nonexistent-plan-id",
        }))
    assert result is None


@pytest.mark.asyncio
async def test_mcp_get_plan_by_date_and_actor(client, agile_project):
    async with client:
        await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-03",
            "actor": "test-actor",
        })
        result = get_result(await client.call_tool("pm_get_plan", {
            "plan_date": "2026-09-03",
            "actor": "test-actor",
        }))
    assert result is not None
    assert result["actor"] == "test-actor"


# ---------------------------------------------------------------------------
# pm_update_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_update_plan_notes(client, agile_project):
    async with client:
        created = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-10",
            "actor": "test-actor",
        }))
        result = get_result(await client.call_tool("pm_update_plan", {
            "plan_id": created["id"],
            "notes": "Updated notes",
        }))
    assert result["notes"] == "Updated notes"


@pytest.mark.asyncio
async def test_mcp_update_plan_complete_no_items(client, agile_project):
    """Completing a plan with no items succeeds."""
    async with client:
        created = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-11",
            "actor": "test-actor",
        }))
        result = get_result(await client.call_tool("pm_update_plan", {
            "plan_id": created["id"],
            "status": "completed",
        }))
    assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# pm_delete_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_delete_plan_returns_true(client, agile_project):
    async with client:
        created = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-20",
            "actor": "test-actor",
        }))
        result = get_result(await client.call_tool("pm_delete_plan", {
            "plan_id": created["id"],
        }))
    assert result is True


@pytest.mark.asyncio
async def test_mcp_delete_plan_not_found_returns_false(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_delete_plan", {
            "plan_id": "nonexistent",
        }))
    assert result is False


# ---------------------------------------------------------------------------
# pm_list_plans
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_list_plans_returns_list(client, agile_project):
    async with client:
        await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-25",
            "actor": "list-actor",
        })
        result = get_result(await client.call_tool("pm_list_plans", {
            "actor": "list-actor",
        }))
    assert isinstance(result, list)
    assert len(result) >= 1


@pytest.mark.asyncio
async def test_mcp_list_plans_date_filter(client, agile_project):
    async with client:
        await client.call_tool("pm_create_plan", {
            "plan_date": "2026-09-26",
            "actor": "date-actor",
        })
        result = get_result(await client.call_tool("pm_list_plans", {
            "actor": "date-actor",
            "date_from": "2026-09-26",
            "date_to": "2026-09-26",
        }))
    assert len(result) == 1


# ---------------------------------------------------------------------------
# pm_add_plan_item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_add_plan_item(client, plannable_task):
    async with client:
        plan = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-10-01",
            "actor": "test-actor",
        }))
        result = get_result(await client.call_tool("pm_add_plan_item", {
            "plan_id": plan["id"],
            "node_id": plannable_task.id,
            "planned_minutes": 60,
        }))
    assert result is not None
    assert result["node_id"] == plannable_task.id
    assert result["planned_minutes"] == 60
    assert result["display_order"] == 1


# ---------------------------------------------------------------------------
# pm_remove_plan_item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_remove_plan_item(client, plannable_task):
    async with client:
        plan = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-10-05",
            "actor": "test-actor",
        }))
        item = get_result(await client.call_tool("pm_add_plan_item", {
            "plan_id": plan["id"],
            "node_id": plannable_task.id,
        }))
        result = get_result(await client.call_tool("pm_remove_plan_item", {
            "item_id": item["id"],
        }))
    assert result is True


@pytest.mark.asyncio
async def test_mcp_remove_plan_item_not_found(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_remove_plan_item", {
            "item_id": "nonexistent",
        }))
    assert result is False


# ---------------------------------------------------------------------------
# pm_reorder_plan_item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_reorder_plan_item(client, agile_project):
    task2 = create_node(agile_project.id, node_type="task", title="Task B")
    task3 = create_node(agile_project.id, node_type="task", title="Task C")
    async with client:
        plan = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-10-10",
            "actor": "test-actor",
        }))
        i1 = get_result(await client.call_tool("pm_add_plan_item", {
            "plan_id": plan["id"],
            "node_id": task2.id,
        }))
        i2 = get_result(await client.call_tool("pm_add_plan_item", {
            "plan_id": plan["id"],
            "node_id": task3.id,
        }))
        result = get_result(await client.call_tool("pm_reorder_plan_item", {
            "item_id": i2["id"],
            "new_position": 1,
        }))
    assert result["display_order"] == 1


# ---------------------------------------------------------------------------
# pm_update_plan_item
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_update_plan_item(client, plannable_task):
    async with client:
        plan = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-10-15",
            "actor": "test-actor",
        }))
        item = get_result(await client.call_tool("pm_add_plan_item", {
            "plan_id": plan["id"],
            "node_id": plannable_task.id,
            "planned_minutes": 30,
        }))
        result = get_result(await client.call_tool("pm_update_plan_item", {
            "item_id": item["id"],
            "outcome": "partial",
            "outcome_notes": "Got halfway",
        }))
    assert result["outcome"] == "partial"
    assert result["outcome_notes"] == "Got halfway"


@pytest.mark.asyncio
async def test_mcp_update_plan_item_omit_does_not_clear(client, plannable_task):
    """Omitting a field in pm_update_plan_item leaves it unchanged (UNSET mapping)."""
    async with client:
        plan = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-10-16",
            "actor": "test-actor",
        }))
        item = get_result(await client.call_tool("pm_add_plan_item", {
            "plan_id": plan["id"],
            "node_id": plannable_task.id,
            "planned_minutes": 45,
        }))
        # Update only outcome — planned_minutes omitted so should stay 45
        result = get_result(await client.call_tool("pm_update_plan_item", {
            "item_id": item["id"],
            "outcome": "completed",
        }))
    assert result["planned_minutes"] == 45  # Not cleared


# ---------------------------------------------------------------------------
# pm_get_weekly_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_get_weekly_plan_structure(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_weekly_plan", {
            "week_start_date": "2026-10-07",  # A Wednesday
            "actor": "test-actor",
        }))
    assert result is not None
    assert "week_start" in result
    assert "week_end" in result
    assert "days" in result
    assert len(result["days"]) == 7
    assert "summary" in result
    for slot in result["days"]:
        assert isinstance(slot, list)


@pytest.mark.asyncio
async def test_mcp_get_weekly_plan_wednesday_snaps_to_monday(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_weekly_plan", {
            "week_start_date": "2026-10-07",  # Wednesday
        }))
    # week_start must be Monday Oct 5
    week_start = result["week_start"]
    if isinstance(week_start, str):
        week_start = date.fromisoformat(week_start)
    assert week_start == date(2026, 10, 5)


# ---------------------------------------------------------------------------
# pm_get_monthly_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_get_monthly_plan_structure(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_monthly_plan", {
            "year": 2026,
            "month": 11,
        }))
    assert result is not None
    assert result["year"] == 2026
    assert result["month"] == 11
    assert result["days_in_month"] == 30  # November has 30 days
    assert "total_planned_items" in result
    assert "milestones" in result
    assert "per_actor" in result


# ---------------------------------------------------------------------------
# pm_plan_vs_actual — actor is required (non-optional)
# ---------------------------------------------------------------------------


def test_mcp_plan_vs_actual_actor_is_required():
    """pm_plan_vs_actual must declare actor as a required (non-optional) parameter."""
    from taskyn.mcp.server import pm_plan_vs_actual
    sig = inspect.signature(pm_plan_vs_actual)
    actor_param = sig.parameters["actor"]
    # Required = no default value
    assert actor_param.default is inspect.Parameter.empty, (
        "pm_plan_vs_actual.actor must be a required parameter, not optional"
    )


@pytest.mark.asyncio
async def test_mcp_plan_vs_actual_structure(client, agile_project):
    async with client:
        await client.call_tool("pm_create_plan", {
            "plan_date": "2026-11-01",
            "actor": "test-actor",
        })
        result = get_result(await client.call_tool("pm_plan_vs_actual", {
            "plan_date": "2026-11-01",
            "actor": "test-actor",
        }))
    assert result is not None
    assert "planned_items" in result
    assert "unplanned_items" in result
    assert "summary" in result
    assert "overall_delta" in result["summary"]


# ---------------------------------------------------------------------------
# pm_carry_over_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_carry_over_plan(client, plannable_task):
    async with client:
        source = get_result(await client.call_tool("pm_create_plan", {
            "plan_date": "2026-11-10",
            "actor": "test-actor",
        }))
        await client.call_tool("pm_add_plan_item", {
            "plan_id": source["id"],
            "node_id": plannable_task.id,
        })
        result = get_result(await client.call_tool("pm_carry_over_plan", {
            "source_plan_id": source["id"],
            "target_date": "2026-11-11",
            "actor": "test-actor",
        }))
    assert result is not None
    assert result["source_plan_id"] == source["id"]
    assert "target_plan" in result
    assert "carried_count" in result
    assert "skipped" in result
    assert result["carried_count"] == 1


# ---------------------------------------------------------------------------
# pm_get_methodology_info — can_be_planned is present for all methodologies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_methodology_info_includes_can_be_planned_classic_agile(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_methodology_info", {
            "project_id": agile_project.id,
        }))
    node_types = result["node_types"]
    for nt_name, nt_info in node_types.items():
        assert "can_be_planned" in nt_info, (
            f"can_be_planned missing from node_type '{nt_name}' in classic_agile"
        )


@pytest.mark.asyncio
async def test_mcp_methodology_info_task_is_plannable_in_classic_agile(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_methodology_info", {
            "project_id": agile_project.id,
        }))
    node_types = result["node_types"]
    assert node_types["task"]["can_be_planned"] is True
    assert node_types["story"]["can_be_planned"] is False


@pytest.mark.asyncio
async def test_mcp_methodology_info_can_be_planned_spec_driven(client, temp_db):
    company = create_company("Spec Co")
    spec_project = create_project(company.id, "Spec Project", Methodology.SPEC_DRIVEN)
    async with client:
        result = get_result(await client.call_tool("pm_get_methodology_info", {
            "project_id": spec_project.id,
        }))
    node_types = result["node_types"]
    for nt_name, nt_info in node_types.items():
        assert "can_be_planned" in nt_info, (
            f"can_be_planned missing from '{nt_name}' in spec_driven"
        )
    # todo is plannable; spec/requirement/design/task are not
    assert node_types["todo"]["can_be_planned"] is True
    assert node_types["spec"]["can_be_planned"] is False


@pytest.mark.asyncio
async def test_mcp_methodology_info_can_be_planned_learning(client, temp_db):
    company = create_company("Learn Co")
    learn_project = create_project(company.id, "Learn Project", Methodology.LEARNING)
    async with client:
        result = get_result(await client.call_tool("pm_get_methodology_info", {
            "project_id": learn_project.id,
        }))
    node_types = result["node_types"]
    for nt_name, nt_info in node_types.items():
        assert "can_be_planned" in nt_info, (
            f"can_be_planned missing from '{nt_name}' in learning"
        )
    # activity is plannable; subject and topic are not
    assert node_types["activity"]["can_be_planned"] is True
    assert node_types["subject"]["can_be_planned"] is False
    assert node_types["topic"]["can_be_planned"] is False


@pytest.mark.asyncio
async def test_mcp_methodology_info_also_includes_can_have_assignee(client, agile_project):
    async with client:
        result = get_result(await client.call_tool("pm_get_methodology_info", {
            "project_id": agile_project.id,
        }))
    node_types = result["node_types"]
    for nt_name, nt_info in node_types.items():
        assert "can_have_assignee" in nt_info, (
            f"can_have_assignee missing from node_type '{nt_name}'"
        )


# ---------------------------------------------------------------------------
# Bug-fix regression tests (B4) — "all actors" view via MCP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mcp_list_plans_no_actor_returns_all_actors(client, agile_project):
    """B4: pm_list_plans with actor=None must return plans for all actors, not just default."""
    from taskyn.core.planning import create_plan
    create_plan(plan_date=date(2026, 11, 1), actor="alice")
    create_plan(plan_date=date(2026, 11, 1), actor="bob")

    async with client:
        result = get_result(await client.call_tool("pm_list_plans", {}))

    assert result is not None
    actors_in_result = {p["actor"] for p in result}
    assert "alice" in actors_in_result, "alice's plan should appear when actor is omitted"
    assert "bob" in actors_in_result, "bob's plan should appear when actor is omitted"


@pytest.mark.asyncio
async def test_mcp_get_weekly_plan_no_actor_returns_all_actors(client, agile_project):
    """B4: pm_get_weekly_plan with actor omitted must aggregate all actors' plans."""
    from taskyn.core.planning import create_plan
    # 2026-11-02 is a Monday; create plans for two actors on that day
    create_plan(plan_date=date(2026, 11, 2), actor="alice")
    create_plan(plan_date=date(2026, 11, 2), actor="bob")

    async with client:
        result = get_result(await client.call_tool("pm_get_weekly_plan", {
            "week_start_date": "2026-11-02",
        }))

    assert result is not None
    # The Monday slot (index 0) should contain plans for BOTH alice and bob
    monday_plans = result["days"][0]
    actors_in_monday = {p["actor"] for p in monday_plans}
    assert "alice" in actors_in_monday, "alice should appear in all-actors weekly view"
    assert "bob" in actors_in_monday, "bob should appear in all-actors weekly view"


@pytest.mark.asyncio
async def test_mcp_get_monthly_plan_no_actor_has_per_actor_breakdown(client, agile_project):
    """B4: pm_get_monthly_plan with actor omitted must populate per_actor breakdown."""
    from taskyn.core.planning import create_plan, add_plan_item
    p_alice = create_plan(plan_date=date(2026, 11, 5), actor="alice")
    p_bob = create_plan(plan_date=date(2026, 11, 6), actor="bob")
    task = create_node(agile_project.id, node_type="task", title="Monthly Task")
    add_plan_item(plan_id=p_alice["id"], node_id=task.id, planned_minutes=60)
    add_plan_item(plan_id=p_bob["id"], node_id=task.id, planned_minutes=30)

    async with client:
        result = get_result(await client.call_tool("pm_get_monthly_plan", {
            "year": 2026,
            "month": 11,
        }))

    assert result is not None
    # per_actor must be non-empty when actor is omitted
    assert len(result["per_actor"]) >= 2, (
        "per_actor breakdown must contain entries for each actor when actor is omitted"
    )
    per_actor_names = {entry["actor"] for entry in result["per_actor"]}
    assert "alice" in per_actor_names
    assert "bob" in per_actor_names
