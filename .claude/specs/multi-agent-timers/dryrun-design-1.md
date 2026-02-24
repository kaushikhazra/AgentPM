# Design Dry-Run Report #1

**Document**: `.claude/specs/multi-agent-timers/design.md`
**Reviewed**: 2026-02-24

---

## Critical Gaps (must fix before implementation)

### [C1] CLI timer commands broken — `stop` and `status` don't pass actor

- **Pass**: Pass 7 (Edge Cases & Boundaries) + Pass 2 (Data Flow Trace)
- **What**: The CLI uses `actor="cli"` for `start_timer` and `log_time` (lines 29, 114 of `cli/timer.py`). But `stop_timer()` and `timer_status()` call `get_active_timer()` with **no actor argument** (lines 44, 68). After the design's change, `get_active_timer(actor=None)` queries `WHERE actor IS NULL`, which will NOT find the "cli"-scoped timer.
- **Risk**: After implementation, `taskyn timer stop` and `taskyn timer status` silently report "No active timer" even when a CLI timer is running. The CLI becomes unusable for time tracking.
- **Fix**: Add `cli/timer.py` to the Files Changed table. Both `stop_timer()` and `timer_status()` must call `get_active_timer(actor="cli")`. The `stop_timer` CLI function must also pass `actor="cli"` consistently.

### [C2] Requirement doc incorrectly states "CLI already passes actor=None"

- **Pass**: Pass 1 (Completeness Check)
- **What**: The Out of Scope section in `requirement.md` says "the CLI already passes `actor=None`". The CLI actually passes `actor="cli"` (line 29, 49, 114 of `cli/timer.py`). This incorrect assumption propagated to the design's "no CLI changes needed" statement.
- **Risk**: The assumption shields the CLI from review, leaving C1 unfixed.
- **Fix**: Correct the requirement's Out of Scope section. Replace "No CLI changes needed" with a note that CLI `stop` and `status` commands need actor-scoping.

### [C3] `stop_timer()` return value missing `actor` field

- **Pass**: Pass 2 (Data Flow Trace)
- **What**: The current `stop_timer()` constructs a **new** `TimeEntry` in its return statement (lines 143-152 of `time_entry.py`), manually copying fields from `entry`. The design's Section 2.2 says "rest unchanged — stop logic, propagation" but doesn't add `actor=entry.actor` to this manual construction. The returned TimeEntry will have `actor=None` regardless of the actual stored value.
- **Risk**: Any caller that uses the return value of `stop_timer()` (including MCP's `pm_stop_timer` which calls `.model_dump()`) will report `actor: null` for all stopped timers.
- **Fix**: Add `actor=entry.actor` to the return TimeEntry construction in `stop_timer()`. Explicitly mention this in Section 2.2 instead of "rest unchanged."

---

## Warnings (should fix, may cause issues)

### [W1] Web backend's `TASKYN_ACTOR` not specified — may share scope with agents

- **Pass**: Pass 3 (Interface Contract Validation)
- **What**: The design's Section 5.2 states "GET /timer/current calls pm_get_active_timer which now scopes to the MCP server's actor." But the design doesn't specify what `TASKYN_ACTOR` the web backend's MCP server should be configured with. The default is `"mcp"` (from `get_actor()` in `server.py:24`), which is the same default every other MCP client gets.
- **Risk**: If the web backend and an agent both use the default `"mcp"` actor, the web UI's start/stop will interfere with that agent's timer — exactly the problem this feature solves.
- **Suggestion**: Add a decision to the Decisions Log: "Web backend MCP server must set `TASKYN_ACTOR=web`." Add a note in Section 5 or the Files Changed table (e.g., `docker-compose.yml` env config).

### [W2] Empty string actor creates invisible scope

- **Pass**: Pass 7 (Edge Cases & Boundaries)
- **What**: The design doesn't validate the `actor` parameter. If someone passes `actor=""` (empty string), SQLite's `WHERE actor IS ""` creates a scope distinct from both NULL and any named actor. This scope would be invisible in the UI (actor badge shows empty string).
- **Risk**: Subtle bugs if an env var is set to empty string (`TASKYN_ACTOR=`).
- **Suggestion**: Add a guard in `start_timer()` and `get_active_timer()`: normalize empty string to None, or raise `ValidationError`. One line of code, prevents a class of confusion.

### [W3] Existing test `test_auto_stop_on_new_start` will fail without update

- **Pass**: Pass 1 (Completeness Check)
- **What**: The test at `test_time_entry.py:68-87` starts two timers without passing `actor`, then calls `get_active_timer()` without actor. After the change, `get_active_timer()` → `get_active_timer(actor=None)` still works (NULL scope). But `start_timer(task1.id)` without actor creates a NULL-actor timer, then `start_timer(task2.id)` without actor auto-stops it via `get_active_timer(actor=None)`. This should actually still work. However, the design's Files Changed table says "Update existing tests, add multi-actor concurrency tests" without specifying which tests break or what new tests are needed.
- **Risk**: Test strategy is underspecified. Implementer may miss updating tests or may not add critical multi-actor tests.
- **Suggestion**: Enumerate the new test cases needed: (1) two actors start timers concurrently — neither kills the other, (2) actor-A stops only their own timer, (3) `get_active_timers()` returns all, (4) `complete_node` with actor scoping, (5) CLI actor="cli" round-trip. The existing tests should continue to pass as-is (they use actor=None scope).

---

## Observations (worth discussing)

### [O1] `start_node` works transitively but isn't mentioned in design Section 3

The design's Section 3 (Workflow Changes) explicitly covers `complete_node` and `submit_for_review` but not `start_node`. Since `start_node` calls `start_timer(node_id, actor=actor)` and the core `start_timer` is changed to scope by actor, it works correctly by inheritance. But an implementer reading only Section 3 might not realize `start_node` is also affected and might skip testing it.

### [O2] Multiple SQLite writer processes — pre-existing but amplified

Multi-agent means multiple MCP server processes writing to the same SQLite file concurrently. SQLite serializes writes via file-level locks, which can cause "database is locked" errors under load. This is a pre-existing architectural concern (not introduced by this design) but multi-agent makes it more likely. WAL mode would help but isn't enabled. Not in scope for this design, but worth a future note.

### [O3] `pm_get_active_timers` does N+1 queries for node titles

The new `pm_get_active_timers()` tool (Section 4.2) calls `get_node(entry.node_id)` in a loop for each active timer. With many concurrent agents, this is N+1 queries. The current `pm_get_active_timer` has the same pattern for a single timer. For the expected scale (2-5 concurrent agents), this is fine. If it ever becomes a concern, a JOIN-based query would be better.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 3        | 3        | 3            |

**Verdict**: **FAIL — needs revision**

The CLI breakage (C1, C2) is a showstopper — the design incorrectly assumes the CLI passes `actor=None` when it actually passes `actor="cli"`. The `stop_timer` return value gap (C3) would cause incorrect data in all API responses. All three criticals are easy fixes (add CLI to files changed, fix the return value, correct the requirement doc), but they must be addressed before implementation.
