# Design Dry-Run Report #2

**Document**: `.claude/specs/multi-agent-timers/design.md`
**Reviewed**: 2026-02-24

---

## Critical Gaps (must fix before implementation)

_None found. All 3 criticals from Dry-Run #1 have been addressed._

| Dryrun-1 Finding | Resolution |
|-------------------|------------|
| C1: CLI stop/status don't pass actor | Section 7 added with exact code for `stop_timer()` and `timer_status()` scoped to `actor="cli"` |
| C2: Requirement says "CLI passes actor=None" | Out of Scope corrected to state CLI uses `actor="cli"` and needs stop/status updates |
| C3: `stop_timer()` return missing actor | Section 2.2 explicitly includes `actor=entry.actor` in the return TimeEntry construction |

---

## Warnings (should fix, may cause issues)

### [W1] `log_time()` missing empty-string actor normalization (D9 gap)

- **Pass**: Pass 7 (Edge Cases & Boundaries) + Pass 2 (Data Flow Trace)
- **What**: Decision D9 adds `actor = actor or None` to normalize empty strings, but Section 2.6 (`log_time`) only shows the INSERT change — no normalization guard. `start_timer()` (Section 2.1) has the guard. `log_time()` does not.
- **Risk**: `log_time(node_id, 30, actor="")` would store `actor=""` in the database. This creates an invisible actor scope: entries with `actor=""` won't be found by `get_active_timer(actor=None)` and show as an empty badge in the UI. While `log_time` entries are immediately closed (not active timers), the inconsistency pollutes the time entries list.
- **Suggestion**: Add `actor = actor or None` at the top of `log_time()` — same one-line guard as `start_timer()`. Mention this in Section 2.6.

### [W2] `docker-compose.yml` change doesn't specify which service or include dev compose

- **Pass**: Pass 7 (Edge Cases & Boundaries)
- **What**: Section 5.3 says "set `TASKYN_ACTOR=web` in `docker-compose.yml`" and the Files Changed table says "Set `TASKYN_ACTOR=web` on web backend MCP service (D8)." But there are two services (`taskyn-core` and `taskyn-web`) and the env var must go on `taskyn-core` (where `get_actor()` runs), not on `taskyn-web`. Additionally, `docker-compose.dev.yml` exists and likely needs the same change, but isn't listed in Files Changed.
- **Risk**: An implementer might set the env var on `taskyn-web` (where it has no effect since that service doesn't run an MCP server with `get_actor()`), or might miss updating the dev compose file.
- **Suggestion**: Clarify in Section 5.3: "Change `TASKYN_ACTOR=mcp` to `TASKYN_ACTOR=web` on the `taskyn-core` service in both `docker-compose.yml` and `docker-compose.dev.yml`."

---

## Observations (worth discussing)

### [O1] `log_time()` return value — text note, not code block

Section 2.6 states "Return value includes `actor=actor`" as a text note after the SQL code block. Every other section (2.1, 2.2) shows the full return statement in a code block. The current `log_time()` (lines 197-206 of `time_entry.py`) manually constructs the return TimeEntry without `actor`. An implementer scanning code blocks might miss the text-only note. Not a correctness issue (the note is there), but less explicit than the `stop_timer` fix.

### [O2] Dryrun-1 observations remain valid

The three observations from Dryrun-1 (O1: `start_node` works transitively, O2: SQLite writer concurrency, O3: N+1 queries in `pm_get_active_timers`) remain unchanged and are still accurate. None require design changes for this iteration.

---

## Verification of Dryrun-1 Warnings

| Dryrun-1 Warning | Resolution |
|-------------------|------------|
| W1: Web backend TASKYN_ACTOR not specified | D8 added, Section 5.3 added, `docker-compose.yml` in Files Changed (but see W2 above for specificity gap) |
| W2: Empty string actor creates invisible scope | D9 added, `actor = actor or None` guard in Section 2.1 (but see W1 above for `log_time` gap) |
| W3: Test strategy underspecified | Section 8 added with 8 named test cases covering multi-actor concurrency, scoping, normalization, and CLI round-trip |

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 0        | 2        | 2            |

**Verdict**: **PASS WITH WARNINGS**

The three critical gaps from Dry-Run #1 have all been resolved. The two remaining warnings are minor specificity issues (empty-string guard missing from one function, ambiguous Docker service target) that are easy to address during implementation. The design is ready for task planning.
