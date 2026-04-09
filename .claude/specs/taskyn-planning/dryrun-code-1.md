# Dryrun Code Review — Taskyn Planning
**Date**: 2026-04-09
**Reviewer**: VH (Opus)
**Verdict**: NEEDS FIXES


## Bugs Found

### B1: `create_plan` inline items skip `planned_minutes` and `display_order` validation

**Location**: `core/planning.py`, `create_plan()`, lines 201–240

The `add_plan_item` function correctly validates `planned_minutes >= 0` and `position >= 1`. But the inline item creation path in `create_plan` only calls `_validate_node_plannable()` — it never checks:
- `planned_minutes >= 0` (negative values silently inserted)
- `display_order >= 1` (zero or negative orders silently inserted)

```python
# create_plan — current code (no bounds validation)
for idx, item in enumerate(items, start=1):
    item_id = uuid4().hex
    order = item.get("display_order", idx)           # ← no >= 1 check
    minutes = item.get("planned_minutes")             # ← no >= 0 check
    execute("INSERT INTO plan_items ...", (...))
```

**Impact**: Invalid data in the database. A caller passing `{"node_id": "x", "planned_minutes": -30}` or `{"node_id": "x", "display_order": 0}` succeeds silently.

**Fix**: Add validation before the insert loop:
```python
if items:
    for item in items:
        _validate_node_plannable(item["node_id"])
        pm = item.get("planned_minutes")
        if pm is not None and pm < 0:
            raise ValidationError("planned_minutes must be >= 0")
        order = item.get("display_order")
        if order is not None and order < 1:
            raise ValidationError("display_order must be >= 1")
```

---

### B2: `create_plan` inline items — duplicate `node_id` causes unhandled exception

**Location**: `core/planning.py`, `create_plan()`, lines 226–240

If the same `node_id` appears twice in the inline `items` list, the second INSERT hits the `UNIQUE(plan_id, node_id)` constraint. Unlike `add_plan_item()` which catches this:
```python
except Exception as exc:
    if "UNIQUE constraint" in str(exc):
        raise ValidationError(f"Node '{node_id}' is already in plan '{plan_id}'")
```

The `create_plan` inline path has no such handler. The raw `sqlite3.IntegrityError` propagates uncaught, potentially leaving the database in a partially-committed state (plan created, first item inserted, second item fails — all within the `serialized()` block, so it should roll back, but the error message is user-hostile).

**Fix**: Either pre-validate for duplicate node_ids before the loop:
```python
node_ids_seen = set()
for item in items:
    nid = item["node_id"]
    if nid in node_ids_seen:
        raise ValidationError(f"Duplicate node_id '{nid}' in items list")
    node_ids_seen.add(nid)
```
Or wrap each insert with the same UNIQUE constraint handler used in `add_plan_item`.

---

### B3: `carry_over_plan` with explicit `item_ids` re-carries already-carried items

**Location**: `core/planning.py`, `carry_over_plan()`, lines 1359–1372

When `item_ids=None`, the function correctly handles all five outcome states:
- `pending`, `partial` → carry
- `completed`, `dropped` → skip as `already_resolved`
- `carried_over` → silently ignore (comment: "already processed")

But when `item_ids` is explicitly provided, the filter only checks for `COMPLETED` and `DROPPED`:
```python
if row["outcome"] in (PlanOutcome.COMPLETED, PlanOutcome.DROPPED):
    skipped.append({...})
else:
    items_to_carry.append(row)  # ← CARRIED_OVER falls through here!
```

An item with `outcome=carried_over` passes this check and gets re-carried. This overwrites its `carried_to_plan_id` (breaking the link to the original target plan) and creates a duplicate item in the new target.

**Impact**: Corrupts the carry-over chain. Plan A → B link is silently replaced with Plan A → C, while Plan B still has the orphaned copy.

**Fix**: Add `PlanOutcome.CARRIED_OVER` to the skip condition:
```python
if row["outcome"] in (PlanOutcome.COMPLETED, PlanOutcome.DROPPED, PlanOutcome.CARRIED_OVER):
    skipped.append({
        "item_id": iid,
        "node_id": row["node_id"],
        "reason": "already_resolved" if row["outcome"] != PlanOutcome.CARRIED_OVER else "already_carried",
    })
```

---

### B4: MCP horizon/list tools always resolve actor — "all actors" view unreachable

**Location**: `mcp/server.py`, `pm_list_plans()` (line 1561), `pm_get_weekly_plan()` (line 1704), `pm_get_monthly_plan()` (line 1730)

All three tools pass `actor=_resolve_actor(actor)` to the core function. Since `_resolve_actor(None)` returns `get_actor()` (the transport default), passing `actor=None` to the MCP tool always becomes `actor="<default_actor>"`.

This blocks the "all actors" aggregate views:
- **TP-5**: "If actor is omitted, returns plans for all actors" — unreachable via MCP
- **TP-6**: "If actor is omitted, returns aggregate across all actors" — unreachable via MCP
- **list_plans**: Cannot list all actors' plans — always filtered to default actor

The core functions handle `actor=None` correctly (they query without actor filter). The MCP layer prevents this.

**Impact**: Multi-actor planning views — one of the core features of weekly/monthly horizons — are completely inaccessible. The `per_actor` breakdown in monthly plans is always empty (because an actor filter is always applied, and the code returns `per_actor: []` when actor is not None).

**Fix**: For filter-only tools, pass `actor` directly without `_resolve_actor`:
```python
# pm_list_plans, pm_get_weekly_plan, pm_get_monthly_plan
actor=actor,  # None means "all actors" — do NOT resolve
```
Keep `_resolve_actor` only for tools where actor is the entity owner (create_plan) or the action performer (activity log).


## Design Deviations

### D1: Activity log `action` value for plan creation

**Design**: `action="created"` | **Code**: `action="plan_created"`

The code uses `"plan_created"` which is more specific than the design's `"created"`. This is arguably better for filtering (distinguishes plan creation from other entity creations), but it deviates from the design's activity logging table.

### D2: Activity log missing `old_value`/`new_value` in multiple operations

The design specifies detailed old/new values for activity logging. The code omits them in several cases:

| Operation | Design `old_value` | Code `old_value` | Design `new_value` | Code `new_value` |
|-----------|-------------------|-------------------|--------------------|--------------------|
| Create plan | — | — | date | *missing* |
| Update plan notes | old notes | *missing* | new notes | *missing* |
| Complete plan | `"active"` | *missing* | `"completed"` | *missing* |
| Delete plan | date | *missing* | — | — |
| Carry over item | source plan.id | *missing* | target plan.id | target plan.id |

These don't affect functionality but reduce the auditability of the activity log. When reviewing past activity, you'd see "plan updated" but not what changed.

### D3: MCP `pm_get_plan` docstring promises unreachable "any actor" path

The MCP tool docstring says:
> "(plan_date, any) — any actor on that date when actor omitted"

But `_resolve_actor(actor)` always fills in a default actor, so this path in the core function is never reached from MCP:
```python
elif plan_date is not None:  # no actor
    plan_row = fetchone("SELECT * FROM plans WHERE date = ?", ...)
```

The docstring should be updated to reflect the actual behavior (defaults to transport actor).

### D4: Schema index name difference

**Design**: `idx_plan_items_plan` | **Code**: `idx_plan_items_plan_order`

Same composite index `(plan_id, display_order)`, just different names. The code's name is more descriptive. No functional impact.


## Warning Compliance

| Warning | Status | Evidence |
|---------|--------|----------|
| **C1**: ON DELETE CASCADE → SET NULL | **FIXED** | Schema: `node_id TEXT REFERENCES nodes(id) ON DELETE SET NULL`. `node_id` is nullable. `get_plan()` detects `node_id IS NULL` and sets `node_deleted=True`. Comment in schema explains NULL UNIQUE behavior. |
| **C2**: pm_get_methodology_info serialization | **FIXED** | server.py line 425-426: includes `can_be_planned`, `can_have_assignee`, and `valid_statuses` in the manual dict. |
| **C3**: Weekly multi-actor structure | **FIXED** | Each day slot is `list[plan_dict]` (empty list when no plans). Code groups by date string and builds 7-slot list. Tested by `test_weekly_plan_two_actors_same_day_both_appear`. |
| **W1**: UNSET sentinel at MCP boundary | **ADDRESSED** | Design explicitly documents: "MCP layer maps None → UNSET, provides no clear-to-null path." MCP tools use `field if field is not None else UNSET` pattern. Convention is consistent. |
| **W2**: `planned_minutes >= 0`, `position >= 1` | **PARTIALLY ADDRESSED** | `add_plan_item`: validates both ✅. `update_plan_item`: validates planned_minutes ✅. `create_plan` inline: **neither validated** ❌ (see B1). |
| **W3**: Reorder algorithm correctness | **ADDRESSED** | 4-step algorithm implemented correctly. Position validated against total count BEFORE removal. 14 reorder tests covering all specified edge cases (same-position, first↔last, 2-item list, 1-item list, middle forward/backward, out-of-bounds). Contiguous orders verified after multiple reorders. |
| **W4**: `pm_plan_vs_actual` actor required | **FIXED** | MCP tool signature: `actor: str` (required, no default). Design says `actor: str` without `| None`. Matches requirement TP-7. |
| **W5**: Midnight spanning documented | **ADDRESSED** | `plan_vs_actual` docstring: "An entry that spans midnight counts entirely toward the start date — this is known behaviour, not a bug (W5 / documented limitation)." |
| **W6**: Terminal-status nodes allowed | **ADDRESSED** | `add_plan_item` docstring: "Terminal-status nodes (done, cancelled) are intentionally allowed." Test: `test_add_plan_item_terminal_status_node_allowed` verifies. No soft warning implemented — documented as explicit non-goal. |
| **W7**: Past date carry-over allowed | **ADDRESSED** | `carry_over_plan` validates `target_date > source_date` only (not vs today). Docstring: "Carrying to a past date that is still after the source date is allowed — this supports retroactive plan reconstruction (W7)." Test: `test_carry_over_past_target_after_source_succeeds`. |
| **W8**: `completed_at IS NULL` for milestones | **FIXED** | `get_monthly_plan` line 1096: `AND m.completed_at IS NULL`. Code comment explicitly references W8 fix. Test: `test_monthly_plan_milestones_use_completed_at_is_null` verifies open vs completed filtering. |


## Code Quality Issues

### CQ1: `_parse_date` silently returns today for non-date types

```python
def _parse_date(value) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return _today()  # ← silent fallback
```

If an unexpected type (e.g., `int`, `None`) reaches this function, it silently returns today's date instead of raising an error. This could mask bugs upstream. Consider raising `ValueError` for unexpected types.

### CQ2: `plan_vs_actual` N+1 query pattern

For each planned item, a separate SQL query fetches time entries:
```python
for item in plan["items"]:
    te_row = fetchone(
        "SELECT COALESCE(SUM(duration_minutes), 0) AS actual "
        "FROM time_entries WHERE node_id = ? AND actor = ? AND date(started_at) = ?",
        (node_id, actor, plan_date.isoformat()),
    )
```

A plan with 15 items issues 15 individual queries. Could be optimized with a single query grouping by `node_id`:
```sql
SELECT node_id, COALESCE(SUM(duration_minutes), 0) AS actual
FROM time_entries
WHERE node_id IN (?, ?, ...) AND actor = ? AND date(started_at) = ?
GROUP BY node_id
```

Not a correctness issue, but worth noting for plans with many items.

### CQ3: `get_plan` date-only lookup has non-deterministic ordering

```python
elif plan_date is not None:  # no actor, no plan_id
    plan_row = fetchone(
        "SELECT * FROM plans WHERE date = ?",
        (plan_date.isoformat(),),
    )
```

When multiple actors have plans on the same date, which plan is returned is non-deterministic (no ORDER BY). This path is unreachable from MCP (due to `_resolve_actor`), but it exists in the core function. Consider adding `ORDER BY actor ASC` for determinism, or documenting the behavior.

### CQ4: Monthly `per_actor` breakdown excludes actors with empty plans

In `get_monthly_plan`, per-actor data is populated from the `item_rows` loop. An actor who has plans but no items in them won't appear in `per_actor` at all, while they ARE counted in the global `days_with_plans`. This creates an inconsistency between global and per-actor counts.

### CQ5: No dead code or TODO comments found

The code is clean — no abandoned code paths, no TODO markers, no commented-out experiments. Import patterns are consistent (lazy imports where needed to avoid circular deps, top-level imports otherwise).


## Test Coverage Gaps

### Untested paths in `create_plan`:
1. **Negative `planned_minutes` in inline items** — would pass silently (B1)
2. **`display_order < 1` in inline items** — would pass silently (B1)
3. **Duplicate `node_id` in inline items list** — would crash with raw SQLite error (B2)

### Untested paths in `carry_over_plan`:
4. **Re-carrying an already-carried item via explicit `item_ids`** — would corrupt carry chain (B3)
5. **Carrying items with `node_id=None` (deleted nodes)** — code allows it, but behavior is untested

### Untested paths in `plan_vs_actual`:
6. **Plan with deleted nodes (node_id=None)** — the `continue` path at line 1173 is untested

### Untested edge cases in `update_plan_item`:
7. **Setting `outcome=None` at core level** — would violate NOT NULL constraint. MCP prevents this, but core function doesn't guard against it.

### Untested integration paths:
8. **ON DELETE SET NULL via actual node deletion** — tests simulate with `UPDATE plan_items SET node_id = NULL` instead of deleting the node through the FK cascade. A test that actually deletes a node and verifies the plan item survives would be stronger.
9. **Weekly plan `actual_minutes` from time entries** — no test creates time entries and verifies the weekly summary's `actual_minutes` field
10. **Monthly plan `actual_minutes` from time entries** — same gap for monthly view
11. **Monthly plan `per_actor.actual_minutes`** — the per-actor time entry aggregation is untested

### No MCP-layer tests:
12. Tests exercise core functions directly — no tests for MCP tool wrappers. UNSET mapping, date parsing from strings, and `_resolve_actor` behavior in the MCP layer are untested. The B4 bug (actor always resolved) would have been caught by an MCP-layer test that verifies `pm_get_weekly_plan(actor=None)` returns all-actor results.


## Requirement Coverage Matrix

| Story | Title | Verdict | Notes |
|-------|-------|---------|-------|
| **TP-1** | Daily plan as first-class entity | **Pass** | Plan CRUD works correctly. UNIQUE(date, actor) enforced. Activity logging present (minor deviations in old/new values — D1, D2). |
| **TP-2** | Plan items with priority ordering | **Pass** | All item operations work. Ordering, shifting, recompaction correct. Validation on add_plan_item is thorough. |
| **TP-3** | Query a daily plan | **Pass** | All lookup paths work. Enrichment correct. Deleted-node handling correct (ON DELETE SET NULL + node_deleted flag). |
| **TP-4** | Plan item outcomes | **Pass** | All 5 outcomes defined as enum. Completion gate works (pending items block plan completion). |
| **TP-5** | Weekly plan horizon | **Partial** | Core function fully correct (7-slot list, multi-actor support, snapping, summary stats). **MCP layer blocks "all actors" view** (B4) — violates "If actor is omitted, returns plans for all actors." |
| **TP-6** | Monthly plan horizon | **Partial** | Core function fully correct (days_with_plans, outcomes, milestones with completed_at IS NULL, per_actor breakdown). **MCP layer blocks "all actors" aggregate** (B4) — violates "If actor is omitted, returns aggregate across all actors." Per_actor is always empty via MCP. |
| **TP-7** | Plan vs actual comparison | **Pass** | Delta computation correct. Unplanned work surfaced. Actor required in MCP (W4 fix). Summary totals accurate. |
| **TP-8** | Carry over incomplete items | **Pass with warning** | Core logic correct for the normal path. Target plan creation/append works. Source items marked. Duplicate skip works. **BUT**: explicit `item_ids` can re-carry already-carried items (B3 — edge case but real data corruption risk). |
| **TP-9** | Scheduling eligibility | **Pass** | `can_be_planned` on NodeTypeDefinition. All 3 methodologies set correct values. Validation in `add_plan_item` and `create_plan` inline. `pm_get_methodology_info` includes `can_be_planned`. |


## Verdict Rationale

**NEEDS FIXES.** The core planning logic is well-implemented — the data model is sound, the reorder algorithm is correct and thoroughly tested, the design's critical issues (C1–C3) and most warnings (W1–W8) were properly addressed. Test coverage is good for the happy paths and many edge cases.

However, four bugs require fixes before production use:

1. **B1 + B2** (inline item validation gaps in `create_plan`): These allow invalid data and unhandled exceptions through a common entry point. Fix: add the same validation that `add_plan_item` already performs.

2. **B3** (re-carry bug): A carry-over with explicit `item_ids` can corrupt the carry chain by re-carrying already-carried items. Fix: one line — add `PlanOutcome.CARRIED_OVER` to the skip condition.

3. **B4** (MCP actor resolution blocks multi-actor views): This is the most impactful bug. The weekly and monthly horizon tools — designed to give a bird's-eye view across all actors — are restricted to single-actor views at the MCP layer. The core functions work perfectly; the MCP wiring defeats them. Fix: don't use `_resolve_actor` for filter-only parameters.

None of these require architectural changes. B1, B2, and B3 are localized fixes. B4 requires changing 3 lines in server.py (pass `actor` directly instead of `_resolve_actor(actor)` for the three affected tools).

The activity logging deviations (D1, D2) are cosmetic — the log entries exist and capture the entity_type, entity_id, action, and actor correctly. The missing old/new values reduce auditability but don't break functionality. These can be addressed in a follow-up.

**Recommended fix priority:**
1. **B4** — Blocks TP-5 and TP-6 acceptance criteria
2. **B3** — Data corruption risk (carry-over chain)
3. **B1 + B2** — Input validation gaps (defense in depth)
4. **D2** — Activity log completeness (nice to have)
