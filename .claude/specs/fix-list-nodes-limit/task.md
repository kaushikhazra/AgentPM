# Tasks: Fix list_nodes Default Limit

- [x] Update `list_nodes()` in `graph/nodes.py` to change `limit` default from `100` to `None`
  - [x] Change signature: `limit: int | None = None`
  - [x] Conditionally append `LIMIT ?` clause only when `limit` is not `None`
  _US-1, US-2_

- [x] Add/update test for `list_nodes()` to verify no truncation with default limit
  - [x] All 38 node/MCP tests pass — no regressions
  - [x] Explicit limit still works when passed (existing tests confirm)
  _US-1, US-2_

- [ ] Verify fix end-to-end
  - [ ] Confirm SAIDR project stats now include epics (requires MCP server restart)
  - [ ] Confirm `pm_list_nodes` for SAIDR returns all 104 nodes (requires MCP server restart)
  _US-1, US-2_
