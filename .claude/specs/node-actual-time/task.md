# Node Actual Time - Tasks

## Backend

- [x] Add `actual_time INTEGER DEFAULT 0` column to nodes table
  - [x] Add column to `schema.sql`
  - [x] Add migration in `connection.py` for existing databases
  _US-4_

- [x] Add `actual_time` field to Node Pydantic model in `models.py`
  _US-4_

- [x] Implement `propagate_actual_time(node_id)` in `time_entry.py`
  - [x] Calculate own time from time_entries (seconds precision)
  - [x] Sum children's `actual_time` if node has children
  - [x] Walk up parent chain recursively
  - [x] Runs synchronously (background thread removed — SQLite single-connection)
  _US-2, US-3_

- [x] Add propagation triggers to time operations
  - [x] Call after `stop_timer()`
  - [x] Call after `log_time()`
  - [x] Call after `delete_time_entry()`
  _US-3_

- [x] Add propagation triggers to edge operations
  - [x] Call after parent edge created (propagate to new parent)
  - [x] Call after parent edge deleted (propagate to old parent)
  _US-2_

- [x] Backfill existing data
  - [x] Calculate `actual_time` for all leaf nodes from time_entries
  - [x] Calculate `actual_time` for parent nodes bottom-up
  _US-1_

## Frontend

- [x] Add `actual_time: number` to Node TypeScript interface
  _US-4_

- [x] Create `formatDuration(seconds)` utility function
  - [x] < 60 → "45s"
  - [x] < 3600 → "12m 30s"
  - [x] >= 3600 → "2h 15m"
  - [x] 0 → empty string (don't display)
  _US-1_

- [x] Display `actual_time` on node cards in ProjectDetailPage
  _US-1_

- [x] Display `actual_time` on NodeDetailPage
  - [x] Replace rollup.total_time_minutes usage with node.actual_time
  _US-1, US-2_

## Validation

- [x] Test propagation: log time on leaf → parent's `actual_time` updates
  _US-2, US-3_

- [x] Test propagation: delete time entry → parent's `actual_time` decreases
  _US-3_

- [x] Test backfill: existing time entries produce correct `actual_time`
  _US-1_

- [x] Test UI: node list shows formatted time
  _US-1_

- [x] Test UI: node detail shows correct aggregated time
  _US-2_
