# Node Actual Time - Design

## Approach: Write-Time Propagation
Instead of calculating rollup on every read (current approach — N+1 queries via `get_node_rollup`), store `actual_time` directly on each node and propagate changes up the parent edge chain on writes. Reads become O(1).

## Schema Change

Add `actual_time` column to `nodes` table:
```sql
ALTER TABLE nodes ADD COLUMN actual_time INTEGER DEFAULT 0;
```
- Type: `INTEGER` (seconds)
- Default: `0`
- Leaf node value: sum of own time entries in seconds
- Parent node value: sum of children's `actual_time`

## Propagation Function: `propagate_actual_time(node_id)`

**Location**: `src/taskyn/core/time_entry.py` (co-located with time operations)

**Algorithm**:
1. Recalculate the node's own `actual_time`:
   - If node has children → `SELECT SUM(actual_time) FROM nodes WHERE id IN (children)`
   - If leaf node → calculate from time entries (see Time Calculation below)
   - A node with BOTH time entries and children: `own_entries_time + sum(children.actual_time)`
2. Update the node's `actual_time` in DB
3. Walk up parent edges: find parent via `edges WHERE source_id = node_id AND edge_type = 'parent'`
4. Recursively propagate to parent (repeat from step 1)
5. Stop when no more parents exist

**Time Calculation from entries** (for leaf/own time):
- Use `started_at` and `ended_at` timestamps for precision: `SUM(CAST((julianday(ended_at) - julianday(started_at)) * 86400 AS INTEGER))`
- For entries with `ended_at IS NULL` (running timer): exclude from stored `actual_time` (active timers are ephemeral; the UI shows running time separately via the TimerWidget)
- For manual entries (where `started_at == ended_at`): use `duration_minutes * 60`

**Execution**: Run in a `threading.Thread(daemon=True)` so the caller (stop_timer, log_time, delete_time_entry) returns immediately.

## Trigger Points

Call `propagate_actual_time(node_id)` after:

| Function | File | When |
|----------|------|------|
| `stop_timer()` | `time_entry.py` | After timer is stopped and duration calculated |
| `log_time()` | `time_entry.py` | After manual entry is created |
| `delete_time_entry()` | `time_entry.py` | After entry is deleted |
| Edge created (parent type) | `edges.py` | After a parent edge is created (child moved under a parent) |
| Edge deleted (parent type) | `edges.py` | After a parent edge is deleted (child detached) |

Note: `start_timer()` does NOT trigger propagation — running timers have no `actual_time` until stopped.

## Frontend Changes

### Node List (ProjectDetailPage)
- Display `node.actual_time` on each node card
- Format using a shared `formatDuration(seconds)` utility:
  - `< 60s` → "45s"
  - `< 60m` → "12m 30s"
  - `>= 60m` → "2h 15m"
  - `0` → don't display (keep clean)

### Node Detail Page (NodeDetailPage)
- Replace current `rollup.total_time_minutes` with `node.actual_time`
- Use same `formatDuration()` formatter

### TypeScript Type
- Add `actual_time: number` to `Node` interface (always present, default 0)

## Migration / Backfill

No migration framework exists — schema init just runs `schema.sql` via `executescript`.

**For new databases**: Add `actual_time INTEGER DEFAULT 0` to the `CREATE TABLE nodes` in `schema.sql`.

**For existing databases**: In `_init_schema()` in `connection.py`, check if column exists (`PRAGMA table_info(nodes)`) and `ALTER TABLE` if missing. Then run backfill:
1. For each leaf node (no children): calculate `actual_time` from time_entries
2. For parent nodes (bottom-up): sum children's `actual_time`

## Impact on Existing Rollup

The existing `get_node_rollup()` in `rollup.py` and `pm_get_rollup` MCP tool remain untouched for now — they provide additional stats (completion %, blocked count, story points) beyond just time. But `total_time_minutes` in rollup responses could eventually read from `actual_time` instead of recalculating.

## Edge Cases
- Node with no time entries and no children → `actual_time = 0`
- Node with both direct time entries AND children → sum of own entries + sum of children's `actual_time`
- Reparenting (edge delete + create) → both trigger propagation on old and new parent
- Running timer → NOT included in `actual_time` (shown separately by TimerWidget)
- Concurrent propagation (rare) → last-write-wins is acceptable since propagation is idempotent
