# Taskyn Planning — Requirements

## Overview

Taskyn manages work — nodes, statuses, dependencies, time tracking — but has no way to express **intent**. You can't say "work on X tomorrow, then Y, budget 2 hours." Every item sits in an undifferentiated backlog. Planning is what transforms a task list into a daily workflow.

This feature adds **intention-based planning** across day, week, and month horizons. Plans are priority-ordered lists of nodes — not time-blocked calendars. The core entity is the **daily plan**: one actor's intended work for one day, expressed as an ordered list of nodes with optional time budgets.

**Key design decisions:**

- **V is the planner. KH and VH are executors.** V proposes plans, KH course-corrects, VH handles mechanical execution.
- **Intentions, not schedules.** Priority-ordered lists, not time-slot grids. Rigid is a recipe for failure and disappointment.
- **New Plan + PlanItem tables (Option B from research).** Plans are separate entities, not fields bolted onto Node. This gives clean plan-vs-actual separation, ordered agendas, and multi-actor plans without touching the existing data model.
- **MCP-first.** All planning operations are MCP tools. No special UI required — V manages plans programmatically. Frontend is a separate spec later.
- **Cross-project.** A daily plan can include nodes from multiple projects. Plans are scoped by `(date, actor)`, not by project.

---

## User Stories

### TP-1: Daily plan as a first-class entity

**As** V (the planner),
**I want to** create a daily plan for a specific date and actor,
**so that** the day's intended work is captured as a durable, queryable object.

**Acceptance Criteria:**
- A new `Plan` entity exists with: `id` (UUID), `date` (DATE), `actor` (TEXT), `status` (TEXT), `notes` (TEXT?), `created_at`, `updated_at`
- At most one plan per actor per day — enforced by UNIQUE constraint on `(date, actor)`
- Plan statuses: `active` (initial), `completed`
- MCP tool `pm_create_plan(date, actor, notes?, items?)` creates a plan
  - `items` is an optional list of `{node_id, planned_minutes?, display_order?}` for inline item creation
  - If items are provided without explicit `display_order`, order is inferred from list position (1-indexed)
  - Returns error if a plan already exists for that `(date, actor)` pair
- MCP tool `pm_update_plan(plan_id, notes?, status?)` modifies plan metadata
- MCP tool `pm_delete_plan(plan_id)` deletes a plan and all its items
- MCP tool `pm_list_plans(actor?, date_from?, date_to?, status?)` lists plans matching filters
- Activity log records plan creation, update, and deletion

### TP-2: Plan items with priority ordering

**As** V (the planner),
**I want to** add nodes to a plan in priority order with optional time budgets,
**so that** the executor knows what to work on first and how long to budget.

**Acceptance Criteria:**
- A new `PlanItem` entity exists with: `id` (UUID), `plan_id` (FK→Plan), `node_id` (FK→Node), `planned_minutes` (INT?), `display_order` (INT), `outcome` (TEXT), `outcome_notes` (TEXT?), `carried_to_plan_id` (FK→Plan?), `created_at`, `updated_at`
- `display_order` determines priority position — lower number = higher priority
- `planned_minutes` is optional — not every item needs a time budget
- `outcome` defaults to `pending`
- A node cannot appear twice in the same plan — UNIQUE on `(plan_id, node_id)`
- MCP tool `pm_add_plan_item(plan_id, node_id, planned_minutes?, position?)` adds a node to a plan
  - If `position` is omitted, the item appends at the end (max display_order + 1)
  - If `position` is specified, existing items at or below that position shift down by 1
- MCP tool `pm_remove_plan_item(item_id)` removes an item and recompacts display_order gaps
- MCP tool `pm_reorder_plan_item(item_id, new_position)` moves an item to a new position, shifting others accordingly
- MCP tool `pm_update_plan_item(item_id, planned_minutes?, outcome?, outcome_notes?)` updates item fields

### TP-3: Query a daily plan

**As** KH (the executor),
**I want to** see my plan for today,
**so that** I know what V has lined up and in what order.

**Acceptance Criteria:**
- MCP tool `pm_get_plan(date?, actor?, plan_id?)` retrieves a plan with all its items
  - Accepts either a `(date, actor)` pair or a `plan_id` — at least one must be provided
  - If `date` is omitted and no `plan_id` given, defaults to today
  - If `actor` is omitted and no `plan_id` given, defaults to the calling actor via `get_actor()`
- Items are returned ordered by `display_order`
- Each returned item includes PlanItem fields plus enriched node data: `title`, `status`, `node_type`, `project_id`, `project_name`, `estimated_minutes`, `actual_time`
- If no plan exists for the query, returns `null` — not an error
- If a referenced node has been deleted, the item is still returned with `node_deleted: true` and null node fields

### TP-4: Plan item outcomes

**As** V (the planner),
**I want to** track what happened to each planned item at day's end,
**so that** I can measure planning accuracy and improve over time.

**Acceptance Criteria:**
- Valid outcome values: `pending`, `completed`, `partial`, `carried_over`, `dropped`
  - `pending` — not yet resolved (default)
  - `completed` — the node reached a terminal status during or by the plan date
  - `partial` — work happened but the node isn't finished
  - `carried_over` — moved to a future plan (linked via `carried_to_plan_id`)
  - `dropped` — intentionally removed without carrying over
- `outcome_notes` is optional free text (e.g., "blocked by external dependency")
- V sets outcomes via `pm_update_plan_item(item_id, outcome=..., outcome_notes=...)`
- When a plan is marked `completed` via `pm_update_plan(plan_id, status="completed")`, all items must have a non-pending outcome — otherwise the update returns an error listing the unresolved items
- Outcome values are defined as an enum, not raw strings

### TP-5: Weekly plan horizon

**As** V (the planner),
**I want to** see all daily plans for a given week,
**so that** I can assess workload distribution and plan across the week.

**Acceptance Criteria:**
- MCP tool `pm_get_weekly_plan(week_start_date, actor?)` returns an aggregate view
  - `week_start_date` is a Monday; the tool returns plans for Monday through Sunday
  - If `week_start_date` is not a Monday, the tool snaps to the Monday of that week
  - If `actor` is omitted, returns plans for all actors
- Response includes:
  - A 7-element list of daily plans (one per day), each with their items; days without plans are `null`
  - Summary stats: total planned items, total planned minutes, items by outcome, actual minutes worked (from time entries for the week)
- If no plans exist for any day in the week, returns the empty structure (7 null days + zero stats)

### TP-6: Monthly plan horizon

**As** V (the planner),
**I want to** see a summary of planning activity for a given month,
**so that** I can assess longer-term trends and coverage.

**Acceptance Criteria:**
- MCP tool `pm_get_monthly_plan(year, month, actor?)` returns a summary view
  - If `actor` is omitted, returns aggregate across all actors
- Response includes:
  - Days with plans vs total days in the month
  - Total planned items across all daily plans
  - Total planned minutes across all daily plans
  - Outcome distribution: count of items completed, partial, carried over, dropped, pending
  - Actual minutes worked (from time entries for the month)
  - Per-actor breakdown when no actor filter is applied
  - Active milestones with `target_date` in the month (from existing milestone data)
- This is a read-only summary — no new data structures beyond daily plans

### TP-7: Plan vs actual comparison

**As** V (the planner),
**I want to** compare what was planned against what actually happened on a given day,
**so that** I can calibrate future plans based on execution reality.

**Acceptance Criteria:**
- MCP tool `pm_plan_vs_actual(date, actor)` returns a side-by-side comparison
- For each planned item, the response includes:
  - **Planned**: node_id, title, planned_minutes, display_order
  - **Actual**: time entries for that node on that date (summed minutes), current node status, whether the node reached a terminal status
  - **Delta**: `actual_minutes - planned_minutes` (negative = under-budget, positive = over-budget; null if no planned_minutes set)
  - **Outcome**: the PlanItem's stored outcome
- **Unplanned work** is also surfaced: nodes that received time entries on that date but were NOT in the plan, listed separately with their actual minutes and status
- Summary totals: total planned minutes, total actual minutes, planned item count, completed count, unplanned item count, overall delta

### TP-8: Carry over incomplete items

**As** V (the planner),
**I want to** carry unfinished plan items forward to the next day's plan,
**so that** incomplete work is not lost and the next day starts with the right priorities.

**Acceptance Criteria:**
- MCP tool `pm_carry_over_plan(source_plan_id, target_date, item_ids?)` carries items forward
  - `item_ids` is an optional list of specific items to carry over; if omitted, all `pending` and `partial` items are carried over
  - Creates the target plan if it doesn't exist (inherits actor from source plan)
  - If the target plan already exists, appends carried items after existing items
- For each carried item:
  - Source item's `outcome` is set to `carried_over`
  - Source item's `carried_to_plan_id` is set to the target plan's ID
  - A new PlanItem is created in the target plan with the same `node_id` and `planned_minutes`
  - New item's `display_order` continues from the target plan's current maximum
- Items already resolved as `completed` or `dropped` are skipped — only `pending` and `partial` items can be carried over
- If an item's node already exists in the target plan, it is skipped (no duplicates) and a warning is included in the response
- Returns the updated target plan with all items

### TP-9: Scheduling eligibility by methodology

**As** the system,
**I want to** enforce that only plannable node types can be added to plans,
**so that** plans contain actionable work items, not container nodes.

**Acceptance Criteria:**
- `NodeTypeDefinition` gains a new boolean field: `can_be_planned`
- Scheduling eligibility per methodology:
  - **classic_agile**: task = `True`; story = `False`; epic = `False`
  - **spec_driven**: todo = `True`; task/spec/requirement/design = `False`
  - **learning**: activity = `True`; topic = `False`; subject = `False`
- Pattern: leaf work items that can track time are plannable; container nodes are not
- `pm_add_plan_item` and the `items` parameter of `pm_create_plan` validate eligibility before adding
  - Adding a non-plannable node type returns an error: `"Node type '{type}' is not plannable in the {methodology} methodology"`
- `pm_get_methodology_info` includes `can_be_planned` in the node type definition response

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `Plan` table | **New** | SQLite table with UNIQUE(date, actor) |
| `PlanItem` table | **New** | SQLite table with FK to Plan and Node, UNIQUE(plan_id, node_id) |
| `Plan` Pydantic model | **New** | In `db/models.py` |
| `PlanItem` Pydantic model | **New** | In `db/models.py` |
| Schema migration | **Needed** | Add Plan + PlanItem tables to `schema.py` |
| `core/planning.py` | **New** | Business logic for plan CRUD, carry-over, comparison |
| `NodeTypeDefinition` | Exists — needs `can_be_planned` | New boolean field, default `False` |
| All 3 methodology classes | Exist — need update | Set `can_be_planned` on leaf node types |
| MCP server | Exists — needs new tools | ~14 new `pm_*` tools |
| `ActivityLog` | Exists | Needs `"plan"` as a valid entity_type value |
| `time_entries` table | Exists | Read-only for plan-vs-actual queries |
| `nodes` table | Exists | Read-only for item enrichment in plan queries |
| `milestones` table | Exists | Read-only for monthly horizon milestone context |

---

## Out of Scope

- **Frontend/UI** — no planner page changes, no calendar views, no drag-and-drop. A separate spec will address the planning UI after the backend is solid.
- **Time-slot grids** — plans are ordered lists, not "9am–11am" blocks. No time-of-day concept.
- **Calendar integration** — no sync with Google Calendar, Outlook, or iCal.
- **Notification/reminder system** — no alerts for upcoming plan items or overdue work.
- **Recurring tasks** — no "every Monday, schedule X" automation.
- **Due dates on nodes** — Node does not gain date fields. Temporal intent lives in PlanItem, not Node.
- **Actor registry/validation** — actor strings remain free-form, consistent with the existing system.
- **Plan templates** — no "create a plan from a saved template" feature.
- **Velocity-based plan suggestions** — V's planning intelligence lives in the AI, not in Taskyn business logic. Taskyn stores and queries plans; V uses judgment to create them.
- **Cross-day item splitting** — if a task spans multiple days, it appears in multiple daily plans as separate PlanItems. No single-item multi-day span concept.
- **Auto-resolve outcomes from node state** — outcomes are set explicitly by V (or via carry-over). Automatic derivation from node status changes may come later but is not part of this spec.
