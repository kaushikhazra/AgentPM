# Code Dry-Run Report #1

**Scope**: Multi-agent concurrent timers — full stack (schema, core, workflow, CLI, MCP, web API, frontend)
**Design**: `.claude/specs/multi-agent-timers/design.md`
**Reviewed**: 2026-02-24

---

## Bugs (will cause incorrect behavior)

### [B1] `reporting.py:_row_to_time_entry()` missing `actor` field
- **File**: `src/taskyn/core/reporting.py:73-84`
- **Pass**: Pass 2 (Execution Path Trace), Pass 7 (Contract Violations)
- **What**: `reporting.py` has its own `_row_to_time_entry()` that was NOT updated to read `row["actor"]`. The query (`SELECT * FROM time_entries`) returns the `actor` column, but the function doesn't pass it to the `TimeEntry` constructor. The Pydantic default (`actor=None`) silently hides the real value.
- **Impact**: `list_time_entries_since()` returns `TimeEntry` objects with `actor=None` regardless of actual actor. Currently only used by `get_dashboard()` for `today_time_minutes` sum (which uses `duration_minutes`, not `actor`), so no visible behavioral impact today. But any future consumer relying on actor from these entries gets wrong data.
- **Fix**: Add `actor=row["actor"],` to the `TimeEntry()` constructor at line 82. Or better: delete the duplicate function and import `_row_to_time_entry` from `time_entry.py`.

---

## Gaps (missing implementation)

### [G1] `stop()` in TimerProvider doesn't accept `entryId` parameter (D7)
- **File**: `src/taskyn/web/frontend/src/providers/TimerProvider.tsx:105-114`
- **Pass**: Pass 1 (Design Conformance)
- **What**: Design decision D7 says `stop(entryId?)` takes an optional entry ID to stop a specific timer. The `timerApi.stop(entryId?)` API layer already supports this. But `TimerProvider.stop()` takes no parameters — it always calls `timerApi.stop()` without an entry ID, which stops only the "web" actor's timer.
- **Design ref**: Section 6.5 (`stop: (entryId?: string) => Promise<void>`), D7

### [G2] Double polling — `useTimerCurrent` and `useActiveTimers` both active at 1s
- **File**: `src/taskyn/web/frontend/src/providers/TimerProvider.tsx:40-48`
- **Pass**: Pass 1 (Design Conformance), Pass 5 (Resource Management)
- **What**: Design Section 6.5 says "Replace `useTimerCurrent` with `useActiveTimers`". The implementation keeps BOTH hooks polling at 1-second intervals, generating 2 HTTP requests/second to the backend (`GET /timer/current` + `GET /timer/active`). The `/timer/active` response already contains the web actor's timer, making `/timer/current` redundant.
- **Design ref**: Section 6.5 ("Polling: Replace `useTimerCurrent` with `useActiveTimers`")

---

## Warnings (potential issues)

### [W1] Multi-timer view has no per-timer stop buttons
- **File**: `src/taskyn/web/frontend/src/components/organisms/TimerWidget.tsx:17-49`
- **Pass**: Pass 1 (Design Conformance), Pass 2 (Execution Path Trace)
- **What**: When multiple timers are active, the TimerWidget shows a "Stop Mine" button that stops the web actor's timer. The design (Section 6.6) specifies per-timer stop buttons that call `stop(timer.id)`. Without per-timer buttons, a web user cannot stop another actor's timer from the widget — they'd need to navigate to another view.
- **Risk**: Users may expect to be able to stop any visible timer. Blocked by G1 (stop doesn't accept entryId).

### [W2] TimerProvider keeps backward-compat `activeTimer` + `elapsed` (D6 says clean break)
- **File**: `src/taskyn/web/frontend/src/providers/TimerProvider.tsx:16-29`
- **Pass**: Pass 1 (Design Conformance)
- **What**: D6 says "Clean break — all consumers updated in one pass." The implementation keeps both `activeTimer`+`elapsed` (singular, from `useTimerCurrent`) AND `activeTimers`+`elapsedMap` (plural, from `useActiveTimers`). All consumers were updated in the same PR, so the backward-compat fields are not needed by any existing consumer.
- **Risk**: Low. The extra fields work correctly. But they contribute to the double-polling issue (G2) and increase cognitive load for future developers who must understand two parallel state shapes.

---

## Style (code quality, conventions)

### [S1] Duplicate `_row_to_time_entry` across modules
- **File**: `src/taskyn/core/reporting.py:73-84` and `src/taskyn/core/time_entry.py:344-356`
- **What**: Two copies of the same function exist. The `reporting.py` copy is now stale (missing `actor`). Should import from `time_entry.py` or consolidate.

### [S2] Kanban timer format differs from design
- **File**: `src/taskyn/web/frontend/src/pages/KanbanPage.tsx:171`
- **What**: Kanban renders `⏱ {formatted}{t.actor ? ` (${t.actor})` : ''}` while design says `{t.actor ?? 'manual'} · {formatted}`. Functionally equivalent but inconsistent with the design document.

### [S3] TrackerPage hides actor badge when null; design shows "manual"
- **File**: `src/taskyn/web/frontend/src/pages/TrackerPage.tsx:139`
- **What**: `{entry.actor ? <span ...>{entry.actor}</span> : null}` hides the badge when actor is null. Design says `{entry.actor ?? 'manual'}` (always show badge). The implementation choice is arguably better UX (less noise for legacy entries).

---

## Summary

| Bugs | Gaps | Warnings | Style |
|------|------|----------|-------|
| 1    | 2    | 2        | 3     |

**Verdict**: PASS WITH WARNINGS — The one bug (B1) has no visible impact today since the affected field isn't used in the current code path, but it's a data correctness issue that should be fixed. The two gaps (G1, G2) are related: fixing G2 (removing double polling) removes the need for `useTimerCurrent`, and fixing G1 (adding `entryId` to `stop()`) enables per-timer stop buttons (W1). These should be addressed before merge.
