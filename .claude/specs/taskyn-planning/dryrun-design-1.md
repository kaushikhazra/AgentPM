# Dryrun Design Review — Taskyn Planning
**Date**: 2026-04-09
**Reviewer**: VH (Opus)
**Verdict**: PASS WITH WARNINGS


## Critical Issues

### C1: ON DELETE CASCADE on plan_items.node_id contradicts TP-3

**Requirement (TP-3)**: "If a referenced node has been deleted, the item is still returned with `node_deleted: true` and null node fields."

**Design (schema.sql)**: `node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE`

These are mutually exclusive. `ON DELETE CASCADE` deletes the plan_item row when the node is deleted — there is nothing left to return with `node_deleted: true`. The plan item ceases to exist.

**Fix**: Change to `ON DELETE SET NULL` and make `node_id` nullable:
```sql
node_id TEXT REFERENCES nodes(id) ON DELETE SET NULL,
```
Then `get_plan()` can detect `node_id IS NULL` and set `node_deleted: true` on the returned item. The `UNIQUE(plan_id, node_id)` constraint needs a note that NULL node_ids are not constrained by UNIQUE in SQLite (NULLs are always distinct), which is the correct behavior here — multiple deleted-node items can coexist.

**Impact**: Without this fix, plan history is silently destroyed when nodes are deleted. Completed plans lose items, and plan-vs-actual comparisons become inaccurate.

---

### C2: pm_get_methodology_info uses manual serialization — can_be_planned won't auto-appear

**Design claim**: "Since `can_be_planned` is a new dataclass field with a default, it will automatically appear in the dict representation. No tool change needed."

**Reality**: `pm_get_methodology_info` (server.py lines 421–425) manually constructs the dict with only 4 fields:
```python
"initial_status": nt.initial_status,
"terminal_statuses": list(nt.terminal_statuses),
"allowed_transitions": nt.allowed_transitions,
"can_track_time": nt.can_track_time,
```

Fields already omitted from the response: `valid_statuses`, `required_properties`, `optional_properties`, `can_have_assignee`. The new `can_be_planned` will be equally omitted.

**Fix**: The design must explicitly add `can_be_planned` to the manual serialization dict in `pm_get_methodology_info`. Consider also adding `valid_statuses` and `can_have_assignee` while there — they're useful and their absence is arguably a pre-existing bug.

**Impact**: TP-9 requires "pm_get_methodology_info includes `can_be_planned` in the node type definition response." Without the fix, this acceptance criterion fails.

---

### C3: Weekly plan all-actor view is structurally undefined

**Requirement (TP-5)**: "If `actor` is omitted, returns plans for all actors." And: "A 7-element list of daily plans (one per day), each with their items."

**Problem**: The `UNIQUE(date, actor)` constraint means a single day can have multiple plans (one per actor). When `actor` is omitted, the "7-element list where each is a plan dict or None" structure cannot represent multiple plans on the same day.

The design's implementation step says "For each day, call get_plan() or return None" — but `get_plan()` requires an actor for the `(date, actor)` lookup. With no actor filter, which plan do you return for Monday?

**Fix**: When `actor` is None, each day slot should be a **list of plan dicts** (possibly empty) rather than a single plan-or-null. E.g.:
```python
days: list of 7 entries, each is a list[plan_dict]  # empty list = no plans
```
Alternatively, keep the actor parameter required for weekly view, but that contradicts the requirement.

**Impact**: Without clarification, the implementer will have to guess the data structure, likely resulting in a bug or deviation from the requirement.


## Warnings

### W1: UNSET sentinel doesn't survive the MCP boundary

The core functions `update_plan()` and `update_plan_item()` use the `UNSET` sentinel to distinguish "not provided" from "set to None." But the MCP tool signatures use `str | None = None` — FastMCP cannot distinguish between "caller didn't pass the parameter" and "caller passed None."

**Consequence**: If the MCP tool receives `None` for `notes`, should it clear the notes or leave them unchanged? The existing codebase likely has a convention for this (other `pm_update_*` tools face the same issue). The design should either:
- Document the convention explicitly (e.g., "None means don't change; pass empty string to clear")
- Or note that the MCP layer maps `None` → `UNSET` and provides no "clear to null" path

**Risk**: Medium — likely handled by existing convention, but undocumented.

### W2: No validation on planned_minutes or position bounds

- `planned_minutes` has no minimum check — negative values are silently accepted
- `position` in `add_plan_item` and `reorder_plan_item` — the design validates `new_position < 1` but doesn't mention `position = 0` in `add_plan_item`
- `display_order` recompaction starts at 1 (correct), but `_shift_items_down` doesn't validate the `from_position` parameter

**Fix**: Add `planned_minutes >= 0` validation and `position >= 1` validation in both `add_plan_item` and `reorder_plan_item`.

### W3: Reorder algorithm is an off-by-one magnet

The 4-step reorder algorithm (remove → recompact → shift → insert) is correct in theory but requires careful implementation:
1. After removing and recompacting, the item count decreases by 1
2. The `new_position` must be validated against the post-removal count, not the original count
3. The shift-then-insert must use the recompacted state, not the original state

This is the #1 source of bugs in ordered-list implementations. The design describes the algorithm clearly, but the implementer should write exhaustive tests for: move-to-same-position, move-to-first, move-to-last, move-from-first-to-last, move-from-last-to-first, move-in-2-item-list.

### W4: pm_plan_vs_actual actor: required in requirement, optional in design

**Requirement (TP-7)**: `pm_plan_vs_actual(date, actor)` — actor is a required parameter.

**Design (MCP tool)**: `actor: str | None = None` — actor is optional with default to transport actor.

This isn't functionally broken (defaults to transport actor), but it's a spec deviation. If the requirement intent is "always explicit," the MCP tool should make actor required. If the default is acceptable, the requirement should be updated.

### W5: Time entries spanning midnight — date assignment undocumented

`plan_vs_actual` uses `date(started_at) = plan_date` to match time entries to a day. A timer started at 23:30 and stopped at 01:15 would be assigned entirely to the start date. The `duration_minutes` (105 min) would all count toward the start day, even though 75 minutes were worked on the next day.

This is the correct pragmatic choice (splitting entries across midnight would be over-engineered), but it should be documented as a known behavior so users don't report it as a bug.

### W6: No guard against planning terminal-status nodes

A node in "done" or "cancelled" status can be added to a plan. The requirement only restricts by node **type** (`can_be_planned`), not by node **status**. This is likely intentional (you might plan to review a completed node), but it means a plan could contain entirely-completed items, which is misleading.

Consider a soft warning in the response (not a blocking error) when planning a terminal-status node, or document this as an explicit non-goal.

### W7: Carry-over target_date validation allows same day

The design says: `ValidationError: If target_date <= source plan's date`. This means carrying over to the same date is blocked (correct). But what about carrying over to a past date that's still after the source? E.g., source=April 5, target=April 7 (both in the past). This is allowed and probably fine (retroactive plan reconstruction), but worth a conscious decision.

### W8: Monthly milestone query uses hardcoded status 'open'

The design implementation says: `Query milestones WHERE ... AND status = 'open'`. But milestone statuses are not 'open' — looking at the methodology research:
- Milestone statuses appear to be simple strings (the model just has `status (str)`)
- The `complete_milestone()` function sets a `completed_at` timestamp
- There's no evidence that 'open' is a valid milestone status value

**Fix**: The filter should probably be `status != 'completed'` or `completed_at IS NULL` to find active milestones, rather than `status = 'open'`.


## Observations

### O1: Tool count discrepancy (minor)
The requirement's infrastructure table says "~14 new pm_* tools." The design lists exactly 13. The tilde covers it, but note the final count.

### O2: get_actor() responsibility lives in MCP layer only
The core `get_plan()` docstring says "defaults to get_actor() via caller" — but `get_actor()` is an MCP transport concept. The core function should not call `get_actor()` directly. This is the correct layering (MCP calls `_resolve_actor()`, core receives a resolved string), but the docstring implies the core handles it. Clarify that actor resolution happens in the MCP layer, and the core function treats `actor=None` as "no filter" or raises if required.

### O3: Consider index on plan_items(plan_id, display_order)
The design indexes `plan_items(plan_id)` separately, but all ORDER BY queries on plan items will be `WHERE plan_id = ? ORDER BY display_order`. A composite index `(plan_id, display_order)` would serve both the WHERE and the ORDER BY in a single index scan. The current separate index works but is suboptimal.

### O4: _recompact_display_order issues N individual UPDATEs
For a plan with 20 items, removing one item triggers 19 individual UPDATE statements. This is fine for typical plan sizes (5–15 items) but worth noting. If plan sizes ever grow large, consider a single UPDATE with ROW_NUMBER window function (SQLite 3.25+).

### O5: Activity logging for batch item creation in create_plan
When `create_plan` is called with inline `items`, does each item log a separate activity entry? The design doesn't specify. Consider a single "plan_created_with_N_items" activity entry vs N individual "item_added" entries. The former is cleaner for activity feeds; the latter is more auditable. Pick one and document it.

### O6: Carry-over doesn't copy outcome_notes
When carrying over a `partial` item, the source's `outcome_notes` (which might explain why it was partial) are not copied to the new item. The new item starts fresh with `outcome_notes=None`. This is probably correct (the new day is a fresh start), but if the notes contain context about remaining work, they'd be lost.

### O7: No `offset` parameter on `list_plans`
`list_plans` has `limit` but no `offset` for pagination. Existing tools in the codebase may or may not support pagination — check for consistency. For an actor with months of daily plans, scrolling past the first 50 requires date filtering, not offset.


## Requirement Coverage Matrix

| Story | Title | Covered? | Gap |
|-------|-------|----------|-----|
| **TP-1** | Daily plan as first-class entity | ✅ Fully covered | — |
| **TP-2** | Plan items with priority ordering | ✅ Fully covered | — |
| **TP-3** | Query a daily plan | ⚠️ Partially covered | **C1**: ON DELETE CASCADE destroys items instead of preserving with `node_deleted: true` |
| **TP-4** | Plan item outcomes | ✅ Fully covered | — |
| **TP-5** | Weekly plan horizon | ⚠️ Partially covered | **C3**: All-actor view structure undefined for multi-actor days |
| **TP-6** | Monthly plan horizon | ⚠️ Minor gap | **W8**: Milestone status filter uses 'open' which may not exist |
| **TP-7** | Plan vs actual comparison | ✅ Functionally covered | **W4**: actor optionality differs from requirement (functional, not structural) |
| **TP-8** | Carry over incomplete items | ✅ Fully covered | — |
| **TP-9** | Scheduling eligibility | ⚠️ Partially covered | **C2**: pm_get_methodology_info won't expose `can_be_planned` without explicit serialization change |


## Verdict Rationale

**PASS WITH WARNINGS.** The design is solid in its overall architecture — the Plan/PlanItem separation, cross-project scoping, methodology integration, and carry-over logic are all well-thought-out. The three critical issues are all fixable without architectural changes:

- **C1** (CASCADE vs SET NULL) is a one-line schema change + making `node_id` nullable
- **C2** (manual serialization) is adding one line to `pm_get_methodology_info`
- **C3** (weekly multi-actor structure) is a data shape clarification in the return type

None of these require rethinking the design. They're implementation details that would cause bugs if not caught before coding, which is exactly what this review is for.

The warnings (W1–W8) are manageable with awareness — most are validation gaps or documentation needs, not design flaws. The reorder algorithm (W3) deserves extra test coverage.

**Recommendation**: Fix C1, C2, and C3 in the design document before implementation. The warnings can be addressed during implementation as defensive coding practices.
