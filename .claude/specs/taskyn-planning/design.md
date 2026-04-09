# Taskyn Planning — Design

## Module Structure

```
src/taskyn/
├── db/
│   ├── enums.py              # + PlanStatus, PlanOutcome enums
│   ├── models.py             # + Plan, PlanItem models
│   └── schema.sql            # + plans, plan_items tables
├── core/
│   └── planning.py           # NEW — plan CRUD, items, horizons, comparison, carry-over
├── methodologies/
│   ├── base.py               # + can_be_planned on NodeTypeDefinition
│   ├── classic_agile.py      # + can_be_planned per node type
│   ├── spec_driven.py        # + can_be_planned per node type
│   └── learning.py           # + can_be_planned per node type
└── mcp/
    └── server.py             # + 13 new pm_*_plan* tools
```

**Modified files**: `db/enums.py`, `db/models.py`, `db/schema.sql`, `methodologies/base.py`, `methodologies/classic_agile.py`, `methodologies/spec_driven.py`, `methodologies/learning.py`, `mcp/server.py`, `core/__init__.py`

**New files**: `core/planning.py`


## Data Models

### Enums (db/enums.py)

```python
class PlanStatus(str, Enum):
    """Plan lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"


class PlanOutcome(str, Enum):
    """Outcome of a planned item at day's end.

    - PENDING: not yet resolved (default)
    - COMPLETED: node reached a terminal status
    - PARTIAL: work happened but node isn't finished
    - CARRIED_OVER: moved to a future plan (linked via carried_to_plan_id)
    - DROPPED: intentionally removed without carrying over
    """

    PENDING = "pending"
    COMPLETED = "completed"
    PARTIAL = "partial"
    CARRIED_OVER = "carried_over"
    DROPPED = "dropped"
```

### Pydantic Models (db/models.py)

```python
class Plan(BaseModel):
    """Plan model — one actor's intended work for one day."""

    id: str
    date: date
    actor: str
    status: str = "active"          # PlanStatus value
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PlanItem(BaseModel):
    """PlanItem model — a single node in a daily plan."""

    id: str
    plan_id: str
    node_id: str | None = None    # None when the referenced node has been deleted
    planned_minutes: int | None = None
    display_order: int
    outcome: str = "pending"        # PlanOutcome value
    outcome_notes: str | None = None
    carried_to_plan_id: str | None = None
    created_at: datetime
    updated_at: datetime
```


## Schema (db/schema.sql)

Added to the `TRACKING LAYER` section, after `activity_log`:

```sql
-- ============================================================
-- PLANNING LAYER: Intention-based daily plans
-- ============================================================

-- Daily plans: one per actor per day
CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    actor TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date, actor)
);

-- Plan items: ordered nodes within a plan
CREATE TABLE IF NOT EXISTS plan_items (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    node_id TEXT REFERENCES nodes(id) ON DELETE SET NULL,
    -- NOTE: NULL node_ids are not constrained by UNIQUE in SQLite (NULLs are always
    -- distinct), so multiple items with deleted nodes can coexist in the same plan.
    planned_minutes INTEGER,
    display_order INTEGER NOT NULL,
    outcome TEXT NOT NULL DEFAULT 'pending'
        CHECK (outcome IN ('pending', 'completed', 'partial', 'carried_over', 'dropped')),
    outcome_notes TEXT,
    carried_to_plan_id TEXT REFERENCES plans(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(plan_id, node_id)
);

-- Planning indexes
CREATE INDEX IF NOT EXISTS idx_plans_date ON plans(date);
CREATE INDEX IF NOT EXISTS idx_plans_actor ON plans(actor);
CREATE INDEX IF NOT EXISTS idx_plans_date_actor ON plans(date, actor);
CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);
CREATE INDEX IF NOT EXISTS idx_plan_items_plan ON plan_items(plan_id, display_order);
CREATE INDEX IF NOT EXISTS idx_plan_items_node ON plan_items(node_id);
CREATE INDEX IF NOT EXISTS idx_plan_items_outcome ON plan_items(outcome);
CREATE INDEX IF NOT EXISTS idx_plan_items_carried_to ON plan_items(carried_to_plan_id);
```


## Core Planning Module (core/planning.py)

All functions follow existing patterns: raw SQL via `execute`/`fetchone`/`fetchall`/`commit`, `serialized()` for multi-step writes, `log_activity()` for audit trail.

### Internal Helpers

```python
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

from taskyn.db.connection import execute, fetchone, fetchall, commit, serialized
from taskyn.db.models import Plan, PlanItem
from taskyn.db.enums import PlanStatus, PlanOutcome
from taskyn.core.activity import log_activity
from taskyn.exceptions import NotFoundError, ValidationError


# Sentinel for distinguishing "not provided" from "set to None"
UNSET = object()


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def _today() -> date:
    """Get current UTC date."""
    return _now().date()


def _row_to_plan(row) -> Plan:
    """Convert a database row to a Plan model."""
    return Plan(
        id=row["id"],
        date=_parse_date(row["date"]),
        actor=row["actor"],
        status=row["status"],
        notes=row["notes"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def _row_to_plan_item(row) -> PlanItem:
    """Convert a database row to a PlanItem model."""
    return PlanItem(
        id=row["id"],
        plan_id=row["plan_id"],
        node_id=row["node_id"],
        planned_minutes=row["planned_minutes"],
        display_order=row["display_order"],
        outcome=row["outcome"],
        outcome_notes=row["outcome_notes"],
        carried_to_plan_id=row["carried_to_plan_id"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def _get_max_display_order(plan_id: str) -> int:
    """Get the current maximum display_order in a plan (0 if empty)."""
    row = fetchone(
        "SELECT COALESCE(MAX(display_order), 0) as max_order "
        "FROM plan_items WHERE plan_id = ?",
        (plan_id,),
    )
    return row["max_order"] if row else 0


def _shift_items_down(plan_id: str, from_position: int) -> None:
    """Shift display_order of items >= from_position down by 1."""
    execute(
        "UPDATE plan_items SET display_order = display_order + 1, "
        "updated_at = ? WHERE plan_id = ? AND display_order >= ?",
        (_now(), plan_id, from_position),
    )


def _recompact_display_order(plan_id: str) -> None:
    """Recompact display_order to remove gaps (1, 2, 3, ...)."""
    rows = fetchall(
        "SELECT id FROM plan_items WHERE plan_id = ? ORDER BY display_order",
        (plan_id,),
    )
    for idx, row in enumerate(rows, start=1):
        execute(
            "UPDATE plan_items SET display_order = ? WHERE id = ?",
            (idx, row["id"]),
        )


def _validate_node_plannable(node_id: str) -> None:
    """Validate that a node's type is plannable per its project's methodology.

    Raises ValidationError if the node type has can_be_planned=False.
    """
    from taskyn.graph.nodes import get_node
    from taskyn.core.project import get_project
    from taskyn.methodologies import get_methodology

    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)

    project = get_project(node.project_id)
    if project is None:
        return  # Can't validate without project

    methodology = get_methodology(project.methodology)
    if methodology is None:
        return

    node_type_def = methodology.get_node_type(node.node_type)
    if node_type_def is not None and not node_type_def.can_be_planned:
        raise ValidationError(
            f"Node type '{node.node_type}' is not plannable "
            f"in the {methodology.name} methodology"
        )


def _parse_date(value) -> date:
    """Parse a date from SQLite."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    return _today()


def _parse_datetime(value) -> datetime:
    """Parse a datetime from SQLite."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return _now()
```

### Plan CRUD

**UNSET sentinel convention**: In `update_plan()` and `update_plan_item()`, parameters default to `UNSET` (not `None`). `None` means "clear this field"; `UNSET` means "leave unchanged". This matches existing `pm_update_*` conventions in the codebase. The MCP layer maps absent optional parameters to `UNSET` before calling core functions, and provides no "clear to null" path for fields that use this sentinel.

```python
def create_plan(
    plan_date: date,
    actor: str,
    notes: str | None = None,
    items: list[dict] | None = None,
) -> dict:
    """Create a daily plan for a specific date and actor.

    Args:
        plan_date: The date this plan covers.
        actor: Who this plan is for (free-form string).
        notes: Optional freetext notes for the day.
        items: Optional inline items — list of dicts with keys:
               node_id (required), planned_minutes (optional),
               display_order (optional — inferred from list position if omitted).

    Returns:
        Dict with plan fields and items list.

    Raises:
        ValidationError: If a plan already exists for (date, actor),
                         or if any item's node type is not plannable.

    Activity logging: When items are provided inline, logs one "plan_created"
        activity entry for the plan — not individual "item_added" entries per item.
        Subsequent pm_add_plan_item calls log "added" per item as normal.
    """


def get_plan(
    plan_id: str | None = None,
    plan_date: date | None = None,
    actor: str | None = None,
) -> dict | None:
    """Retrieve a plan with all its items and enriched node data.

    Lookup priority:
        1. plan_id — direct lookup
        2. (plan_date, actor) — unique pair lookup
        3. (today, default actor) — convenience default

    At least one of plan_id or (plan_date, actor) should be provided.
    If plan_date is omitted and no plan_id, defaults to today.
    If actor is omitted and no plan_id, defaults to get_actor() via caller.

    Returns:
        Dict with plan fields + items list. Each item enriched with:
            node_title, node_status, node_type, project_id, project_name,
            estimated_minutes, actual_time, node_deleted (bool)
        Items ordered by display_order.
        Returns None if no plan found (not an error).
        If a referenced node has been deleted, item is still returned
        with node_deleted=True and null node fields.
    """


def update_plan(
    plan_id: str,
    notes: str | None = UNSET,
    status: str | None = UNSET,
    actor: str | None = None,
) -> Plan:
    """Update plan metadata.

    Args:
        plan_id: Plan to update.
        notes: New notes (pass None to clear, omit to leave unchanged).
        status: New status. When setting to "completed", all items must
                have non-pending outcomes — otherwise raises ValidationError
                listing unresolved item IDs.
        actor: Actor performing the update (for activity log).

    Raises:
        NotFoundError: If plan not found.
        ValidationError: If completing a plan with pending items.
    """


def delete_plan(plan_id: str, actor: str | None = None) -> bool:
    """Delete a plan and all its items (CASCADE).

    Args:
        plan_id: Plan to delete.
        actor: Actor performing the deletion (for activity log).

    Returns:
        True if deleted, False if plan not found.
    """


def list_plans(
    actor: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Plan]:
    """List plans matching optional filters.

    Args:
        actor: Filter by actor.
        date_from: Include plans on or after this date.
        date_to: Include plans on or before this date.
        status: Filter by plan status ("active" or "completed").
        limit: Max results (default 50).
        offset: Number of results to skip for pagination (default 0).

    Returns:
        List of Plan models ordered by date descending.
    """
```

### Plan Item Operations

```python
def add_plan_item(
    plan_id: str,
    node_id: str,
    planned_minutes: int | None = None,
    position: int | None = None,
    actor: str | None = None,
) -> PlanItem:
    """Add a node to a plan.

    Args:
        plan_id: Target plan.
        node_id: Node to add (supports prefix matching via get_node).
        planned_minutes: Optional time budget in minutes.
        position: Insert position (1-indexed). If omitted, appends at end
                  (max display_order + 1). If specified, existing items at
                  or below that position shift down by 1.
        actor: Actor performing the action (for activity log).

    Returns:
        The created PlanItem.

    Raises:
        NotFoundError: If plan or node not found.
        ValidationError: If node type is not plannable, or node already in plan,
                         or planned_minutes < 0, or position < 1.

    Notes:
        - planned_minutes must be >= 0 if provided.
        - position must be >= 1 if provided.
        - No status validation — terminal-status nodes (done, cancelled) can be
          planned. This is intentional (e.g., planning to review completed work).
    """


def remove_plan_item(item_id: str, actor: str | None = None) -> bool:
    """Remove an item from its plan and recompact display_order.

    Args:
        item_id: PlanItem to remove.
        actor: Actor performing the action (for activity log).

    Returns:
        True if removed, False if item not found.
    """


def reorder_plan_item(
    item_id: str,
    new_position: int,
    actor: str | None = None,
) -> PlanItem:
    """Move a plan item to a new position.

    Algorithm:
        1. Remove item from current position
        2. Recompact remaining items
        3. Shift items at new_position and below down by 1
        4. Insert item at new_position

    Args:
        item_id: PlanItem to move.
        new_position: Target position (1-indexed).
        actor: Actor performing the action (for activity log).

    Returns:
        Updated PlanItem with new display_order.

    Raises:
        NotFoundError: If item not found.
        ValidationError: If new_position < 1 or exceeds item count.

    Test coverage required: move-to-same-position, move-to-first, move-to-last,
        move-from-first-to-last, move-from-last-to-first, move-in-2-item-list,
        move-in-1-item-list.
    """


def update_plan_item(
    item_id: str,
    planned_minutes: int | None = UNSET,
    outcome: str | None = UNSET,
    outcome_notes: str | None = UNSET,
    actor: str | None = None,
) -> PlanItem:
    """Update fields on a plan item.

    Args:
        item_id: PlanItem to update.
        planned_minutes: New time budget (None to clear).
        outcome: New outcome value (validated against PlanOutcome enum).
        outcome_notes: Freetext notes on the outcome (None to clear).
        actor: Actor performing the action (for activity log).

    Returns:
        Updated PlanItem.

    Raises:
        NotFoundError: If item not found.
        ValidationError: If outcome is not a valid PlanOutcome value,
                         or planned_minutes < 0.
    """
```

### Horizon Views

```python
def get_weekly_plan(
    week_start_date: date,
    actor: str | None = None,
) -> dict:
    """Get an aggregate view of daily plans for a 7-day week.

    Args:
        week_start_date: Any date in the target week. Snaps to the Monday
                         of that week if not already a Monday.
        actor: Filter by actor. If omitted, returns plans for all actors.

    Returns:
        Dict with:
            week_start: date (Monday)
            week_end: date (Sunday)
            days: list of 7 entries (Mon-Sun), each is a list[plan_dict]
                  (empty list if no plans exist for that day; multiple plans
                  when actor is omitted and multiple actors have plans on the same day)
            summary:
                total_planned_items: int
                total_planned_minutes: int
                outcomes: dict[str, int]  — count per PlanOutcome value
                actual_minutes: int — sum of time_entries in the week

    Implementation:
        1. Snap week_start_date to Monday: date - timedelta(days=date.weekday())
        2. Query plans WHERE date BETWEEN monday AND sunday, filtered by actor if provided
        3. For each day, collect all matching plans (may be multiple when actor is None);
           each day slot is a list — empty list if no plans, one-or-more dicts if present
        4. Query time_entries WHERE started_at BETWEEN monday 00:00 AND sunday 23:59
           filtered by actor if provided
        5. Aggregate outcomes from all plan_items across the week
    """


def get_monthly_plan(
    year: int,
    month: int,
    actor: str | None = None,
) -> dict:
    """Get a summary of planning activity for a calendar month.

    Args:
        year: e.g. 2026
        month: 1-12
        actor: Filter by actor. If omitted, returns aggregate across all actors.

    Returns:
        Dict with:
            year: int
            month: int
            days_in_month: int
            days_with_plans: int
            total_planned_items: int
            total_planned_minutes: int
            outcomes: dict[str, int]  — count per PlanOutcome value
            actual_minutes: int — sum of time_entries in the month
            per_actor: list[dict] — per-actor breakdown (when no actor filter):
                actor: str
                days_with_plans: int
                total_planned_items: int
                total_planned_minutes: int
                outcomes: dict[str, int]
                actual_minutes: int
            milestones: list[dict] — active milestones with target_date in month:
                id: str
                name: str
                project_id: str
                project_name: str
                target_date: date
                status: str

    Implementation:
        1. Calculate first_day and last_day of month using calendar.monthrange
        2. Query plans WHERE date BETWEEN first_day AND last_day
        3. JOIN plan_items for item counts and planned_minutes
        4. Query time_entries WHERE started_at BETWEEN first_day AND last_day+1
        5. Query milestones WHERE target_date BETWEEN first_day AND last_day
           AND completed_at IS NULL, JOIN projects for project_name
        6. If no actor filter, group by actor for per_actor breakdown
    """
```

### Plan vs Actual Comparison

```python
def plan_vs_actual(
    plan_date: date,
    actor: str,
) -> dict:
    """Compare planned work against actual execution for a specific day.

    For each planned item: shows planned_minutes, actual minutes worked
    (from time_entries on that date), delta, current node status, outcome.

    Also surfaces unplanned work: nodes that received time entries on
    that date but were NOT in the plan.

    Args:
        plan_date: The date to compare.
        actor: The actor whose plan and time entries to examine. Required.

    Notes:
        Time entries are assigned to the date of started_at. A timer spanning
        midnight counts entirely toward the start date (not split across days).
        This is a known behavior, not a bug.

    Returns:
        Dict with:
            date: date
            actor: str
            planned_items: list[dict] — for each item in the plan:
                node_id: str
                title: str
                planned_minutes: int | None
                display_order: int
                actual_minutes: int — summed from time_entries for this node on this date
                current_status: str
                is_terminal: bool — whether node reached a terminal status
                delta_minutes: int | None — actual - planned (None if no planned_minutes)
                outcome: str
                outcome_notes: str | None
            unplanned_items: list[dict] — nodes with time on date but not in plan:
                node_id: str
                title: str
                actual_minutes: int
                current_status: str
                project_id: str
                project_name: str
            summary:
                total_planned_minutes: int
                total_actual_minutes: int — across planned items only
                total_unplanned_minutes: int
                planned_item_count: int
                completed_count: int — items with outcome=completed
                unplanned_item_count: int
                overall_delta: int | None — total_actual - total_planned
                                            (None if no items have planned_minutes)

    Implementation:
        1. Get plan via get_plan(plan_date, actor). If None, empty planned_items.
        2. For each planned item, query time_entries for that node_id
           WHERE actor = ? AND date(started_at) = plan_date.
           Sum duration_minutes. Look up node for current_status.
           Check methodology for is_terminal.
        3. Query all time_entries WHERE actor = ? AND date(started_at) = plan_date.
           Subtract the set of node_ids already in the plan.
           Group remaining by node_id, sum duration_minutes.
        4. Compute summary totals and delta.
    """
```

### Carry Over

```python
def carry_over_plan(
    source_plan_id: str,
    target_date: date,
    item_ids: list[str] | None = None,
    actor: str | None = None,
) -> dict:
    """Carry incomplete items from one plan to another.

    For each carried item:
        1. Source item's outcome → carried_over
        2. Source item's carried_to_plan_id → target plan ID
        3. New PlanItem created in target plan with same node_id
           and planned_minutes, appended after existing items

    Args:
        source_plan_id: Plan to carry items from.
        target_date: Date for the target plan. Creates the target plan
                     if it doesn't exist (inherits actor from source).
                     Appends after existing items if target plan exists.
        item_ids: Optional list of specific PlanItem IDs to carry over.
                  If omitted, carries all items with outcome=pending or partial.
        actor: Actor performing the action (for activity log).

    Returns:
        Dict with:
            source_plan_id: str
            target_plan: dict — the full target plan (same shape as get_plan)
            carried_count: int
            skipped: list[dict] — items skipped with reason:
                item_id: str
                node_id: str
                reason: str  — "already_resolved" | "already_in_target" | "not_found"

    Raises:
        NotFoundError: If source plan not found.
        ValidationError: If target_date <= source plan's date.

    Notes:
        Carrying over to a past date that is still after the source date is allowed
        (e.g., source=April 5, target=April 7, both in the past). This supports
        retroactive plan reconstruction.

    Implementation:
        1. Load source plan, validate exists.
        2. Validate target_date > source.date.
        3. Determine items to carry: if item_ids provided, filter to those;
           otherwise select all items with outcome IN ('pending', 'partial').
        4. Skip items with outcome IN ('completed', 'dropped') — record as
           "already_resolved" in skipped list.
        5. Get or create target plan (same actor as source).
        6. Get current max display_order in target plan.
        7. For each item to carry:
           a. Check if node_id already exists in target plan → skip as
              "already_in_target".
           b. Create new PlanItem in target plan with incremented display_order.
           c. Update source item: outcome='carried_over',
              carried_to_plan_id=target_plan.id.
           d. Log activity on source item.
        8. Return target plan (via get_plan) + carry stats.
    """
```


## Methodology Extension

### NodeTypeDefinition Change (methodologies/base.py)

```python
@dataclass
class NodeTypeDefinition:
    """Defines a valid node type for a methodology."""

    name: str
    valid_statuses: list[str]
    initial_status: str
    terminal_statuses: set[str]
    allowed_transitions: dict[str, list[str]]
    required_properties: list[str] = field(default_factory=list)
    optional_properties: list[str] = field(default_factory=list)
    can_track_time: bool = True
    can_have_assignee: bool = True
    can_be_planned: bool = False      # NEW — defaults to False (safe)
```

### Per-Methodology Settings

**Pattern**: leaf work items that track time are plannable; containers are not.

#### classic_agile.py

| Node Type | `can_be_planned` | Rationale |
|-----------|-----------------|-----------|
| epic      | `False`         | Container — never directly worked |
| story     | `False`         | Container — work lives in tasks |
| task      | `True`          | Leaf work item, tracks time |

```python
"task": NodeTypeDefinition(
    name="task",
    # ... existing fields unchanged ...
    can_be_planned=True,
),
```

#### spec_driven.py

| Node Type   | `can_be_planned` | Rationale |
|-------------|-----------------|-----------|
| spec        | `False`         | Phase container |
| requirement | `False`         | Phase container |
| design      | `False`         | Phase container |
| task        | `False`         | Phase container (implementation grouping) |
| todo        | `True`          | Leaf work item, tracks time |

```python
"todo": NodeTypeDefinition(
    name="todo",
    # ... existing fields unchanged ...
    can_be_planned=True,
),
```

Note: `_phase_node()` helper already sets `can_track_time=False`. The default `can_be_planned=False` covers phase nodes without any change to the helper.

#### learning.py

| Node Type | `can_be_planned` | Rationale |
|-----------|-----------------|-----------|
| subject   | `False`         | Container |
| topic     | `False`         | Container (doesn't track time) |
| activity  | `True`          | Leaf work item, tracks time |

```python
"activity": NodeTypeDefinition(
    name="activity",
    # ... existing fields unchanged ...
    can_be_planned=True,
),
```

### pm_get_methodology_info Response

The existing `pm_get_methodology_info` tool in `server.py` manually constructs a dict for each node type — it does NOT automatically serialize all dataclass fields. The manual dict currently includes only `initial_status`, `terminal_statuses`, `allowed_transitions`, and `can_track_time`.

**Required change**: Add `can_be_planned`, `can_have_assignee`, and `valid_statuses` explicitly to the serialization dict in `pm_get_methodology_info`, alongside the existing fields:

```python
"can_be_planned": nt.can_be_planned,
"can_have_assignee": nt.can_have_assignee,
"valid_statuses": nt.valid_statuses,
```

Without this change, TP-9's acceptance criterion ("pm_get_methodology_info includes `can_be_planned` in the node type definition response") will fail.


## MCP Tools

All new tools are registered on the existing `mcp` FastMCP instance in `server.py`. They follow the established pattern: `@mcp.tool()` decorator, lazy imports from `taskyn.core.planning`, `_resolve_actor()` for actor default, `model_dump()` for serialization.

Date parameters are received as `str` (YYYY-MM-DD) at the MCP layer and parsed to `date` objects before passing to core functions.

### Plan CRUD Tools

```python
@mcp.tool()
def pm_create_plan(
    date: str,
    actor: str | None = None,
    notes: str | None = None,
    items: list[dict] | None = None,
) -> dict:
    """Create a daily plan for a specific date and actor.

    Args:
        date: Plan date (YYYY-MM-DD).
        actor: Who this plan is for. Defaults to transport actor.
        notes: Optional freetext notes.
        items: Optional inline items — list of {node_id, planned_minutes?, display_order?}.
               If display_order is omitted, order is inferred from list position.

    Returns:
        The created plan with items.
    """


@mcp.tool()
def pm_get_plan(
    plan_id: str | None = None,
    date: str | None = None,
    actor: str | None = None,
) -> dict | None:
    """Get a plan with all its items and enriched node data.

    Accepts either plan_id, or (date, actor) pair, or defaults to today.
    Items are returned ordered by display_order, each enriched with node
    title, status, node_type, project_id, project_name.

    Args:
        plan_id: Direct plan lookup.
        date: Plan date (YYYY-MM-DD). Defaults to today if no plan_id.
        actor: Actor filter. Defaults to transport actor if no plan_id.

    Returns:
        Plan dict with items, or null if no plan found.
    """


@mcp.tool()
def pm_update_plan(
    plan_id: str,
    notes: str | None = None,
    status: str | None = None,
) -> dict:
    """Update plan metadata (notes, status).

    When setting status to "completed", all items must have non-pending
    outcomes — otherwise returns an error listing unresolved items.

    Args:
        plan_id: Plan to update.
        notes: New notes.
        status: New status ("active" or "completed").

    Returns:
        Updated plan.
    """


@mcp.tool()
def pm_delete_plan(plan_id: str) -> bool:
    """Delete a plan and all its items.

    Args:
        plan_id: Plan to delete.

    Returns:
        True if deleted.
    """


@mcp.tool()
def pm_list_plans(
    actor: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List plans with optional filters.

    Args:
        actor: Filter by actor.
        date_from: Include plans on or after (YYYY-MM-DD).
        date_to: Include plans on or before (YYYY-MM-DD).
        status: Filter by status ("active" or "completed").
        limit: Max results (default 50).
        offset: Number of results to skip for pagination (default 0).

    Returns:
        List of plan summaries ordered by date descending.
    """
```

### Plan Item Tools

```python
@mcp.tool()
def pm_add_plan_item(
    plan_id: str,
    node_id: str,
    planned_minutes: int | None = None,
    position: int | None = None,
) -> dict:
    """Add a node to a plan.

    Validates that the node type is plannable per its methodology.
    If position is omitted, appends at the end.
    If position is specified, existing items shift down.

    Args:
        plan_id: Target plan.
        node_id: Node to add (supports prefix matching).
        planned_minutes: Optional time budget in minutes.
        position: Insert position (1-indexed). Omit to append.

    Returns:
        The created plan item.
    """


@mcp.tool()
def pm_remove_plan_item(item_id: str) -> bool:
    """Remove a plan item and recompact display_order.

    Args:
        item_id: PlanItem to remove.

    Returns:
        True if removed.
    """


@mcp.tool()
def pm_reorder_plan_item(item_id: str, new_position: int) -> dict:
    """Move a plan item to a new position.

    Args:
        item_id: PlanItem to move.
        new_position: Target position (1-indexed).

    Returns:
        Updated plan item.
    """


@mcp.tool()
def pm_update_plan_item(
    item_id: str,
    planned_minutes: int | None = None,
    outcome: str | None = None,
    outcome_notes: str | None = None,
) -> dict:
    """Update a plan item's fields.

    Args:
        item_id: PlanItem to update.
        planned_minutes: New time budget (minutes).
        outcome: New outcome (pending, completed, partial, carried_over, dropped).
        outcome_notes: Freetext notes on outcome.

    Returns:
        Updated plan item.
    """
```

### Horizon Tools

```python
@mcp.tool()
def pm_get_weekly_plan(
    week_start_date: str,
    actor: str | None = None,
) -> dict:
    """Get all daily plans for a 7-day week with summary stats.

    Snaps to Monday if the given date is not a Monday.

    Args:
        week_start_date: Any date in target week (YYYY-MM-DD).
        actor: Filter by actor. Omit for all actors.

    Returns:
        Week structure with 7 day slots and summary stats.
    """


@mcp.tool()
def pm_get_monthly_plan(
    year: int,
    month: int,
    actor: str | None = None,
) -> dict:
    """Get a planning summary for a calendar month.

    Args:
        year: e.g. 2026
        month: 1-12
        actor: Filter by actor. Omit for aggregate.

    Returns:
        Monthly summary with coverage, outcomes, actual time, milestones.
    """
```

### Comparison & Carry-Over Tools

```python
@mcp.tool()
def pm_plan_vs_actual(
    date: str,
    actor: str,
) -> dict:
    """Compare planned vs actual work for a given day.

    Shows each planned item with actual time entries, delta, and outcome.
    Separately lists unplanned work (nodes with time entries not in the plan).

    Args:
        date: Date to compare (YYYY-MM-DD).
        actor: Actor whose plan and time entries to examine. Required.

    Returns:
        Comparison with planned items, unplanned items, and summary.
    """


@mcp.tool()
def pm_carry_over_plan(
    source_plan_id: str,
    target_date: str,
    item_ids: list[str] | None = None,
) -> dict:
    """Carry incomplete items from one plan to a future date.

    Creates target plan if it doesn't exist. Marks source items as
    carried_over with link to target plan. Skips already-resolved items
    and duplicates.

    Args:
        source_plan_id: Plan to carry items from.
        target_date: Date for target plan (YYYY-MM-DD).
        item_ids: Specific item IDs to carry. Omit for all pending/partial items.

    Returns:
        Target plan with carried items, plus skipped list.
    """
```

### Tool Count Summary

| Category | Tools | Count |
|----------|-------|-------|
| Plan CRUD | pm_create_plan, pm_get_plan, pm_update_plan, pm_delete_plan, pm_list_plans | 5 |
| Plan Items | pm_add_plan_item, pm_remove_plan_item, pm_reorder_plan_item, pm_update_plan_item | 4 |
| Horizons | pm_get_weekly_plan, pm_get_monthly_plan | 2 |
| Comparison | pm_plan_vs_actual | 1 |
| Carry-over | pm_carry_over_plan | 1 |
| **Total** | | **13** |


## Activity Logging

Plan operations log to the existing `activity_log` table using `log_activity()`. The `entity_type` field uses `"plan"` for plan-level operations and `"plan_item"` for item-level operations.

| Operation | entity_type | action | entity_id | old_value | new_value |
|-----------|------------|--------|-----------|-----------|-----------|
| Create plan | `plan` | `created` | plan.id | — | date |
| Update plan notes | `plan` | `updated` | plan.id | old notes | new notes |
| Complete plan | `plan` | `completed` | plan.id | `active` | `completed` |
| Delete plan | `plan` | `deleted` | plan.id | date | — |
| Add item | `plan_item` | `added` | item.id | — | node_id |
| Remove item | `plan_item` | `removed` | item.id | node_id | — |
| Reorder item | `plan_item` | `reordered` | item.id | old position | new position |
| Update item outcome | `plan_item` | `outcome_set` | item.id | old outcome | new outcome |
| Update item minutes | `plan_item` | `updated` | item.id | old minutes | new minutes |
| Carry over item | `plan_item` | `carried_over` | source item.id | source plan.id | target plan.id |

No changes to `ActivityLog` model or `log_activity()` function signature — `entity_type` is already a free-form string with no CHECK constraint in the database.


## Migration Notes

### Schema Addition Strategy

The `plans` and `plan_items` tables use `CREATE TABLE IF NOT EXISTS`, matching every other table in `schema.sql`. Since `_init_schema()` in `connection.py` runs the full `schema.sql` via `executescript()` on every connection, adding the new DDL statements to `schema.sql` is sufficient — they will be created automatically on next startup for both new and existing databases.

### What Needs No Migration

- **New tables** (`plans`, `plan_items`): Handled by `CREATE TABLE IF NOT EXISTS` in `schema.sql`. No `ALTER TABLE` needed.
- **`NodeTypeDefinition.can_be_planned`**: Python dataclass field with a default value (`False`). Not a database column — available immediately when code deploys.
- **Activity log**: `entity_type` is a free-form TEXT column with no CHECK constraint. New values (`"plan"`, `"plan_item"`) work without schema changes.
- **Existing MCP tools**: No signature changes, but `pm_get_methodology_info` requires an explicit dict update — see the pm_get_methodology_info Response section above.

### Implementation Steps

1. **`db/schema.sql`** — Append `plans` + `plan_items` table definitions and indexes after the activity_log section.
2. **`db/enums.py`** — Add `PlanStatus` and `PlanOutcome` enum classes.
3. **`db/models.py`** — Add `Plan` and `PlanItem` Pydantic model classes. Import `date` (already imported).
4. **`methodologies/base.py`** — Add `can_be_planned: bool = False` to `NodeTypeDefinition`.
5. **`methodologies/classic_agile.py`** — Set `can_be_planned=True` on `task`.
6. **`methodologies/spec_driven.py`** — Set `can_be_planned=True` on `todo`.
7. **`methodologies/learning.py`** — Set `can_be_planned=True` on `activity`.
8. **`core/planning.py`** — New module with all functions above.
9. **`core/__init__.py`** — Import and re-export planning functions.
10. **`mcp/server.py`** — Add 13 new tools in a `Planning Tools` section after the existing Reporting/Search section.

### Backward Compatibility

- **Existing databases**: New tables created on next connection via `IF NOT EXISTS`. No data loss, no ALTER TABLE.
- **Existing NodeTypeDefinition instances**: `can_be_planned` defaults to `False`, so all node types remain non-plannable until explicitly opted in per methodology.
- **Existing MCP tools**: `pm_get_methodology_info` requires an explicit code change — `can_be_planned`, `can_have_assignee`, and `valid_statuses` must be manually added to the serialization dict (see pm_get_methodology_info Response section above).
- **Existing activity_log data**: Unaffected. New entity_type values are additive.
