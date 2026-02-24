# Multi-Agent Concurrent Timers — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Scope timers by `actor` column on `time_entries`, not by session or connection | Actor is already plumbed through the entire call chain (MAT-1). Simplest change — one new column, scoped queries. |
| D2 | Use SQLite `IS` operator for NULL-safe actor comparison | `WHERE actor = NULL` doesn't work in SQL. `WHERE actor IS ?` treats NULL as a value. CLI uses `actor="cli"`, MCP uses `get_actor()`, NULL is for pre-migration entries only (MAT-2). |
| D3 | Auto-stop is per-actor, not removed | MAT-4 requires guardrail. Keeping auto-stop (scoped per-actor) is the simplest enforcement — no new error paths, same UX, just narrower blast radius. |
| D4 | `stop_timer(entry_id=...)` ignores actor (admin operation) | MAT-2 explicitly allows stopping by entry_id regardless of actor. Web UI stop buttons use entry_id to stop any timer. |
| D5 | Web UI fetches ALL active timers via new `GET /timer/active` endpoint | TimerProvider needs all timers for dashboard/kanban/tracker (MAT-7/8/9). A single endpoint returning the full list is simpler than N queries. |
| D6 | `TimerProvider` replaces singular `activeTimer` with `activeTimers[]` and `elapsedMap` | Clean break — all consumers updated in one pass. Avoids maintaining two parallel state shapes (MAT-10). |
| D7 | `stop(entryId?)` in TimerProvider takes optional entryId | Web UI needs to stop specific timers from the multi-timer list. Without entryId, stops the "web" actor's timer for backward compat (MAT-7). |
| D8 | Web backend MCP server must set `TASKYN_ACTOR=web` | Without this, the web backend defaults to `"mcp"` — same as agents — and UI start/stop would interfere with agent timers (MAT-10). |
| D9 | Normalize empty string actor to `None` | Prevents invisible actor scopes from misconfigured env vars (`TASKYN_ACTOR=`). Guard in `start_timer()` and `log_time()` — the two functions that INSERT into `time_entries`. |

---

## 1. Schema Migration

### 1.1 Schema Change

Add `actor` column to `time_entries` and an index for the per-actor active timer lookup:

```sql
-- In schema.sql (CREATE TABLE time_entries)
CREATE TABLE IF NOT EXISTS time_entries (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_minutes INTEGER,
    notes TEXT,
    source TEXT DEFAULT 'manual',
    actor TEXT,                                          -- NEW
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- New index (in schema.sql index section)
CREATE INDEX IF NOT EXISTS idx_time_entries_actor_active
    ON time_entries(actor, ended_at);
```

_Traces to: MAT-1 (store actor on entries)_

### 1.2 Migration in `connection.py`

Follow the existing migration pattern in `_run_migrations()`:

```python
# Migration: add actor column to time_entries
te_cols = [
    row[1] for row in _connection.execute("PRAGMA table_info(time_entries)").fetchall()
]
if "actor" not in te_cols:
    _connection.execute("ALTER TABLE time_entries ADD COLUMN actor TEXT")
    _connection.commit()
```

No backfill needed — existing entries get `actor = NULL`. Pre-migration entries from CLI (which used `actor="cli"` at the call site but never stored it) and MCP callers all become NULL-scoped. This is acceptable since there was no multi-actor behavior before migration.

### 1.3 Pydantic Model

```python
# In db/models.py — TimeEntry class
class TimeEntry(BaseModel):
    id: str
    node_id: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    notes: str | None = None
    source: str = "manual"
    actor: str | None = None              # NEW
    created_at: datetime
```

Update `_row_to_time_entry()` in `time_entry.py`:

```python
def _row_to_time_entry(row) -> TimeEntry:
    return TimeEntry(
        id=row["id"],
        node_id=row["node_id"],
        started_at=_parse_datetime(row["started_at"]),
        ended_at=_parse_datetime(row["ended_at"]) if row["ended_at"] else None,
        duration_minutes=row["duration_minutes"],
        notes=row["notes"],
        source=row["source"],
        actor=row["actor"],               # NEW
        created_at=_parse_datetime(row["created_at"]),
    )
```

---

## 2. Core Layer Changes (`time_entry.py`)

### 2.1 `start_timer()` — Actor-scoped auto-stop

```python
def start_timer(
    node_id: str,
    notes: str | None = None,
    source: str = "manual",
    actor: str | None = None,
) -> TimeEntry:
    # Normalize empty string actor to None (D9)
    actor = actor or None

    # ... (node validation unchanged) ...

    # Stop this actor's active timer (not global)
    active = get_active_timer(actor=actor)       # CHANGED: was get_active_timer()
    if active is not None:
        stop_timer(entry_id=active.id, actor=actor)

    entry_id = uuid4().hex
    now = _now()

    execute(
        """
        INSERT INTO time_entries (id, node_id, started_at, notes, source, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (entry_id, node_id, now, notes, source, actor, now),   # actor included
    )
    # ... (log_activity, commit unchanged) ...

    return TimeEntry(
        id=entry_id, node_id=node_id, started_at=now,
        ended_at=None, duration_minutes=None,
        notes=notes, source=source, actor=actor, created_at=now,
    )
```

_Traces to: MAT-1, MAT-4_

### 2.2 `stop_timer()` — Actor-scoped default lookup

```python
def stop_timer(
    node_id: str | None = None,
    entry_id: str | None = None,
    actor: str | None = None,
) -> TimeEntry | None:
    # Find the timer to stop
    if entry_id is not None:
        entry = _get_time_entry(entry_id)           # No actor check (D4)
    elif node_id is not None:
        entry = _get_active_timer_for_node(node_id, actor=actor)  # CHANGED
    else:
        entry = get_active_timer(actor=actor)        # CHANGED: was get_active_timer()

    # ... (stop logic, propagation unchanged) ...

    # Return value MUST include actor from the original entry
    return TimeEntry(
        id=entry.id, node_id=entry.node_id,
        started_at=entry.started_at, ended_at=now,
        duration_minutes=duration,
        notes=entry.notes, source=entry.source,
        actor=entry.actor,                           # ADDED: preserve stored actor
        created_at=entry.created_at,
    )
```

_Traces to: MAT-2_

### 2.3 `get_active_timer()` — Actor-scoped query

```python
def get_active_timer(actor: str | None = None) -> TimeEntry | None:
    """Get the active timer for a specific actor."""
    row = fetchone(
        "SELECT * FROM time_entries WHERE actor IS ? AND ended_at IS NULL "
        "ORDER BY started_at DESC LIMIT 1",
        (actor,),
    )
    if row is None:
        return None
    return _row_to_time_entry(row)
```

_Traces to: MAT-3_

### 2.4 `get_active_timers()` — New function, all active timers

```python
def get_active_timers() -> list[TimeEntry]:
    """Get all active timers across all actors."""
    rows = fetchall(
        "SELECT * FROM time_entries WHERE ended_at IS NULL ORDER BY started_at DESC"
    )
    return [_row_to_time_entry(row) for row in rows]
```

_Traces to: MAT-6_

### 2.5 `_get_active_timer_for_node()` — Actor-scoped

```python
def _get_active_timer_for_node(
    node_id: str,
    actor: str | None = None,
) -> TimeEntry | None:
    """Get the active timer for a specific node and actor."""
    from taskyn.graph.nodes import get_node
    node = get_node(node_id)
    if node is None:
        return None
    node_id = node.id

    row = fetchone(
        "SELECT * FROM time_entries WHERE node_id = ? AND actor IS ? "
        "AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
        (node_id, actor),
    )
    if row is None:
        return None
    return _row_to_time_entry(row)
```

### 2.6 `log_time()` — Store actor

```python
def log_time(
    node_id: str,
    duration_minutes: int,
    notes: str | None = None,
    source: str = "manual",
    actor: str | None = None,
) -> TimeEntry:
    # Normalize empty string actor to None (D9)
    actor = actor or None

    # ... (node validation, _enforce_time_tracking unchanged) ...

    execute(
        """
        INSERT INTO time_entries (id, node_id, started_at, ended_at, duration_minutes, notes, source, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (entry_id, node_id, now, now, duration_minutes, notes, source, actor, now),
    )
    # ... (log_activity, commit, propagate_actual_time unchanged) ...

    return TimeEntry(
        id=entry_id, node_id=node_id,
        started_at=now, ended_at=now,
        duration_minutes=duration_minutes,
        notes=notes, source=source,
        actor=actor,                          # ADDED
        created_at=now,
    )
```

### 2.7 `__init__.py` exports

Add `get_active_timers` to the exports in `core/__init__.py`:

```python
from taskyn.core.time_entry import (
    start_timer,
    stop_timer,
    log_time,
    get_active_timer,
    get_active_timers,       # NEW
    list_time_entries,
    # ...
)
```

---

## 3. Workflow Changes (`workflow.py`)

### 3.1 `complete_node()` — Actor-scoped timer check

```python
def complete_node(node_id: str, actor: str | None = None) -> Node:
    from taskyn.graph import update_node

    node, methodology = _get_node_methodology(node_id)
    node_id = node.id
    done_status = methodology.get_done_status(node.node_type)

    # Stop timer if THIS ACTOR has one running on this node
    active = get_active_timer(actor=actor)           # CHANGED: was get_active_timer()
    if active and active.node_id == node_id:
        stop_timer(actor=actor)

    return update_node(node_id, status=done_status, actor=actor)
```

_Traces to: MAT-5_

### 3.2 `submit_for_review()` — Same pattern

```python
# Line 121-123 changes from:
active = get_active_timer()
if active and active.node_id == node_id:
    stop_timer(actor=actor)

# To:
active = get_active_timer(actor=actor)
if active and active.node_id == node_id:
    stop_timer(actor=actor)
```

---

## 4. MCP Tool Changes (`mcp/server.py`)

### 4.1 `pm_get_active_timer()` — Scoped to calling actor

No signature change. Internal call changes:

```python
@mcp.tool()
def pm_get_active_timer() -> dict | None:
    from taskyn.core import get_active_timer
    from taskyn.graph import get_node

    entry = get_active_timer(actor=get_actor())      # CHANGED: pass actor
    if not entry:
        return None

    node = get_node(entry.node_id)
    return {
        **entry.model_dump(),
        "node_title": node.title if node else None,
        "node": node.model_dump() if node else None,
    }
```

_Traces to: MAT-3_

### 4.2 `pm_get_active_timers()` — New tool

```python
@mcp.tool()
def pm_get_active_timers() -> list[dict]:
    """
    Get all active timers across all agents.

    Returns:
        List of active time entries with node info and actor
    """
    from taskyn.core import get_active_timers
    from taskyn.graph import get_node

    entries = get_active_timers()
    result = []
    for entry in entries:
        node = get_node(entry.node_id)
        result.append({
            **entry.model_dump(),
            "node_title": node.title if node else None,
        })
    return result
```

_Traces to: MAT-6_

### 4.3 `pm_stop_timer()` — No signature change needed

Already passes `actor=get_actor()`. The core `stop_timer` now scopes by actor when no `entry_id` is given:

```python
@mcp.tool()
def pm_stop_timer(entry_id: str | None = None) -> dict | None:
    from taskyn.core import stop_timer
    entry = stop_timer(entry_id=entry_id, actor=get_actor())  # unchanged
    return entry.model_dump() if entry else None
```

---

## 5. Backend API Changes (`web/backend/`)

### 5.1 New endpoint: `GET /timer/active`

In `routes/timer.py`:

```python
@router.get("/active")
async def get_active_timers(
    current_user: User = Depends(get_current_user),
):
    """Get all active timers across all agents."""
    return await call_mcp_tool("pm_get_active_timers", {})
```

_Traces to: MAT-6, MAT-7_

### 5.2 Existing endpoints — no changes

- `POST /timer/start` — calls `pm_start_timer` which passes `get_actor()`. Works.
- `POST /timer/stop` — calls `pm_stop_timer` which passes `get_actor()`. When `entry_id` is provided (from UI stop buttons), stops that specific timer. Works.
- `GET /timer/current` — calls `pm_get_active_timer` which now scopes to the MCP server's actor. Returns the web actor's timer. Works.

### 5.3 Docker configuration — `TASKYN_ACTOR=web`

The web backend's MCP server must set `TASKYN_ACTOR=web` in `docker-compose.yml` so the web UI operates in its own actor scope, separate from CLI (`cli`) and agent MCP clients (their own `TASKYN_ACTOR` values). Without this, the web backend defaults to `"mcp"` and would share scope with any agent that also defaults to `"mcp"` (D8).

---

## 6. Frontend Changes

### 6.1 TypeScript Types (`types/index.ts`)

```typescript
export interface ActiveTimer {
  id: string;
  node_id: string;
  node_title?: string;
  notes: string | null;
  started_at: string;
  actor: string | null;          // NEW
}

export interface TimeEntry {
  id: string;
  node_id: string;
  duration_minutes: number | null;
  notes: string | null;
  started_at: string;
  ended_at: string | null;
  node_title?: string;
  actor?: string | null;         // NEW
}
```

_Traces to: MAT-10_

### 6.2 API Client (`api/timer.ts`)

Add new method:

```typescript
export const timerApi = {
  // ... existing methods unchanged ...

  getActive: () =>
    api.get<ActiveTimer[]>('/timer/active'),     // NEW
};
```

### 6.3 Query Keys (`api/queryKeys.ts`)

```typescript
timer: {
  all: () => ['timer'] as const,
  current: () => [...queryKeys.timer.all(), 'current'] as const,
  active: () => [...queryKeys.timer.all(), 'active'] as const,  // NEW
  list: (projectId?: string) => [...queryKeys.timer.all(), 'list', projectId] as const,
  entry: (id: string) => [...queryKeys.timer.all(), 'entry', id] as const,
}
```

### 6.4 Query Hook (`hooks/queries/useTimerQuery.ts`)

New hook replacing `useTimerCurrent` in TimerProvider:

```typescript
export function useActiveTimers(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.timer.active(),
    queryFn: () => timerApi.getActive(),
    enabled: options?.enabled ?? true,
    refetchInterval: options?.refetchInterval ?? 1_000,
  });
}
```

`useTimerCurrent` remains available but is no longer used by TimerProvider.

### 6.5 TimerProvider (`providers/TimerProvider.tsx`)

Full refactor — singular `activeTimer` + `elapsed` → plural `activeTimers` + `elapsedMap`:

```typescript
export interface TimerContextValue {
  activeTimers: ActiveTimer[];
  elapsedMap: Record<string, number>;   // entryId → elapsed seconds
  loading: boolean;
  start: (nodeId: string, notes?: string) => Promise<void>;
  stop: (entryId?: string) => Promise<void>;  // entryId targets specific timer
  refresh: () => Promise<void>;
}
```

**Polling**: Replace `useTimerCurrent` with `useActiveTimers` (same 1s interval, returns array).

**Elapsed tick**: One interval updates all entries in `elapsedMap`:

```typescript
useEffect(() => {
  if (activeTimers.length > 0) {
    const tick = () => {
      const map: Record<string, number> = {};
      for (const t of activeTimers) {
        map[t.id] = calcElapsed(t.started_at);
      }
      setElapsedMap(map);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  } else {
    setElapsedMap({});
  }
}, [activeTimers, calcElapsed]);
```

**`stop(entryId?)`**: When `entryId` is provided, passes it to `timerApi.stop(entryId)`. When omitted, calls `timerApi.stop()` (stops the web actor's timer).

_Traces to: MAT-10_

### 6.6 TimerWidget (`components/organisms/TimerWidget.tsx`)

Renders a list of active timers instead of one:

```tsx
export function TimerWidget() {
  const { activeTimers, elapsedMap, loading, stop } = useTimer();

  if (activeTimers.length === 0) {
    return (
      <div className="timer-widget">
        <div className="timer-label">No Active Timers</div>
        <div className="timer-display">00:00:00</div>
      </div>
    );
  }

  return (
    <div className="timer-widget">
      <div className="timer-label">
        {activeTimers.length === 1
          ? 'Timer Running'
          : `${activeTimers.length} Timers Running`}
      </div>
      {activeTimers.map((timer) => (
        <div key={timer.id} className="timer-entry">
          <div className="timer-actor">{timer.actor ?? 'manual'}</div>
          <div className="timer-display">
            {formatElapsed(elapsedMap[timer.id] ?? 0)}
          </div>
          <div className="timer-task">
            {timer.node_title ?? timer.node_id.slice(0, 8)}
          </div>
          <button
            className="timer-btn timer-btn-stop"
            onClick={() => void stop(timer.id)}
            disabled={loading}
          >
            <Icon name="stop" size={14} /> Stop
          </button>
        </div>
      ))}
    </div>
  );
}
```

_Traces to: MAT-7_

### 6.7 Dashboard Page

**"Time Tracked Today"** — sum all active timers' elapsed:

```typescript
const totalElapsed = Object.values(elapsedMap).reduce((a, b) => a + b, 0);
const timeTrackedMinutes = Math.floor(totalElapsed / 60);
```

_Traces to: MAT-7_

### 6.8 Tracker Page

**Entry rows** — add actor badge:

```tsx
<span className="time-entry-actor">{entry.actor ?? 'manual'}</span>
```

**Active dot** — check against all active timers:

```typescript
const activeEntryIds = new Set(activeTimers.map(t => t.id));
// In entry rendering:
const isActive = entry.ended_at === null && activeEntryIds.has(entry.id);
```

_Traces to: MAT-8_

### 6.9 Kanban Page

**Multiple tracking indicators** — replace single check with filter:

```typescript
const getTrackingTimers = (nodeId: string): ActiveTimer[] =>
  activeTimers.filter(t => t.node_id === nodeId);
```

**Card rendering**:

```tsx
{trackingTimers.map((t) => (
  <div className="kanban-card-timer" key={t.id}>
    {t.actor ?? 'manual'} · {formatTimerDuration(elapsedMap[t.id] ?? 0)}
  </div>
))}
```

**Left border highlight** — apply when `trackingTimers.length > 0`.

_Traces to: MAT-9_

### 6.10 CSS additions

```css
/* Timer entry within multi-timer widget */
.timer-entry {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.timer-entry:last-child {
  border-bottom: none;
}

/* Actor badge */
.timer-actor {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

/* Tracker actor badge */
.time-entry-actor {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--surface-secondary);
  padding: 1px 6px;
  border-radius: 4px;
}
```

---

## 7. CLI Changes (`cli/timer.py`)

The CLI uses `actor="cli"` for `start` and `log` commands. The `stop` and `status` commands must also scope to `actor="cli"`.

### 7.1 `stop_timer()` — Scope to CLI actor

```python
@app.command("stop")
@handle_errors
def stop_timer():
    """Stop the active timer."""
    from taskyn.core import stop_timer as _stop_timer, get_active_timer

    active = get_active_timer(actor="cli")        # CHANGED: was get_active_timer()
    if active is None:
        console.print("[dim]No active timer[/dim]")
        raise typer.Exit(0)

    entry = _stop_timer(actor="cli")
    # ... (rest unchanged) ...
```

### 7.2 `timer_status()` — Scope to CLI actor

```python
@app.command("status")
@handle_errors
def timer_status():
    """Show the active timer."""
    from taskyn.core import get_active_timer
    from taskyn.graph import get_node

    active = get_active_timer(actor="cli")        # CHANGED: was get_active_timer()
    # ... (rest unchanged) ...
```

_Traces to: MAT-2, MAT-3 (CLI is an actor like any other)_

---

## 8. Test Strategy

### Existing tests — should pass as-is

Tests in `test_time_entry.py` use `actor=None` (default). After the change, `get_active_timer(actor=None)` queries `WHERE actor IS NULL`, which matches NULL-actor entries. The auto-stop behavior is preserved within the NULL scope. No breakage expected.

### New test cases required

| Test | What it validates |
|------|-------------------|
| `test_multi_actor_concurrent_timers` | Agent-A and Agent-B both start timers. Neither kills the other. Both show in `get_active_timers()`. |
| `test_actor_scoped_auto_stop` | Agent-A starts timer on task-1, then task-2. Task-1's timer is auto-stopped. Agent-B's timer is untouched. |
| `test_stop_timer_actor_scoping` | Agent-A and Agent-B both have timers. `stop_timer(actor="A")` only stops A's. B's still running. |
| `test_stop_timer_no_fallback` | Agent-A has no timer. `stop_timer(actor="A")` returns None — does NOT stop Agent-B's timer. |
| `test_complete_node_actor_scoping` | Agent-A and Agent-B both timer same node. `complete_node(node_id, actor="A")` only stops A's timer. |
| `test_get_active_timers_returns_all` | Three actors have timers. `get_active_timers()` returns all three. |
| `test_start_timer_empty_actor_normalized` | `start_timer(node_id, actor="")` creates entry with `actor=None`. |
| `test_cli_actor_round_trip` | `start_timer(actor="cli")`, then `get_active_timer(actor="cli")` finds it, `get_active_timer(actor=None)` does not. |

---

## Files Changed

| File | Change |
|------|--------|
| `src/taskyn/db/schema.sql` | Add `actor TEXT` column to `time_entries` CREATE TABLE, add `idx_time_entries_actor_active` index |
| `src/taskyn/db/connection.py` | Add migration in `_run_migrations()` for `actor` column |
| `src/taskyn/db/models.py` | Add `actor: str \| None = None` to `TimeEntry` |
| `src/taskyn/core/time_entry.py` | Actor-scope `start_timer`, `stop_timer`, `get_active_timer`; add `get_active_timers()`; update `_get_active_timer_for_node`, `_row_to_time_entry`, `log_time` |
| `src/taskyn/core/workflow.py` | Actor-scope timer lookups in `complete_node()`, `submit_for_review()` |
| `src/taskyn/cli/timer.py` | Scope `stop_timer()` and `timer_status()` to `actor="cli"` |
| `src/taskyn/core/__init__.py` | Export `get_active_timers` |
| `src/taskyn/mcp/server.py` | Actor-scope `pm_get_active_timer`; add `pm_get_active_timers` tool |
| `src/taskyn/web/backend/routes/timer.py` | Add `GET /timer/active` endpoint |
| `src/taskyn/web/frontend/src/types/index.ts` | Add `actor` to `ActiveTimer` and `TimeEntry` |
| `src/taskyn/web/frontend/src/api/timer.ts` | Add `getActive()` method |
| `src/taskyn/web/frontend/src/api/queryKeys.ts` | Add `active()` query key |
| `src/taskyn/web/frontend/src/hooks/queries/useTimerQuery.ts` | Add `useActiveTimers` hook |
| `src/taskyn/web/frontend/src/providers/TimerProvider.tsx` | Refactor to `activeTimers[]` + `elapsedMap`, use `useActiveTimers` |
| `src/taskyn/web/frontend/src/hooks/useTimer.ts` | Update `TimerContextValue` type re-export |
| `src/taskyn/web/frontend/src/components/organisms/TimerWidget.tsx` | Render multi-timer list |
| `src/taskyn/web/frontend/src/pages/DashboardPage.tsx` | Sum elapsed from `elapsedMap` |
| `src/taskyn/web/frontend/src/pages/TrackerPage.tsx` | Actor badge on entries, multi-active dots |
| `src/taskyn/web/frontend/src/pages/KanbanPage.tsx` | Multi-card tracking indicators with actor |
| `src/taskyn/web/frontend/src/styles/base.css` | `.timer-entry`, `.timer-actor`, `.time-entry-actor` styles |
| `tests/test_time_entry.py` | Add multi-actor concurrency tests (see Section 8) |
| `docker-compose.yml` | Set `TASKYN_ACTOR=web` on web backend MCP service (D8) |

---

## Future Work (Out of Scope)

- **Configurable max timers per actor** — hardcoded to 1 via auto-stop. Future spec will add a project/system setting.
- **Filter tracker by actor** — all entries shown together for now.
- **Actor management UI** — no way to register or list known actors. Just strings.
- **Per-user timer scoping in web UI** — web backend uses one actor ("web" or MCP default). Multi-user web timer scoping deferred.
