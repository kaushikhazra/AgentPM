# Caller-Scoped Actor for Timer/Workflow — Tasks

## 1. MCP Tool Layer Changes

- [x] Velasari adds `_resolve_actor(actor)` helper to `src/taskyn/mcp/server.py` — _CSA-1, CSA-2, CSA-3, CSA-4_
- [x] Velasari adds `actor: str | None = None` param to `pm_start_timer` in `src/taskyn/mcp/server.py` — _CSA-1_
- [x] Velasari adds `actor: str | None = None` param to `pm_stop_timer` in `src/taskyn/mcp/server.py` — _CSA-2_
- [x] Velasari adds `actor: str | None = None` param to `pm_start_node` in `src/taskyn/mcp/server.py` — _CSA-3_
- [x] Velasari adds `actor: str | None = None` param to `pm_complete_node` in `src/taskyn/mcp/server.py` — _CSA-3_
- [x] Velasari adds `actor: str | None = None` param to `pm_get_active_timer` in `src/taskyn/mcp/server.py` — _CSA-4_
- [x] Velasari updates docstrings on all 5 tools to document actor parameter — _CSA-1, CSA-2, CSA-3, CSA-4_
- [x] Velasari runs existing test suite to confirm no regressions — _CSA-1, CSA-2, CSA-3, CSA-4_

## 2. Actor Override Tests

- [x] Velasari creates `tests/test_mcp_actor_override.py` with test fixtures — _CSA-5_
- [x] Velasari writes `test_start_timer_with_explicit_actor` — _CSA-1_
- [x] Velasari writes `test_start_timer_no_actor_uses_default` — _CSA-1_
- [x] Velasari writes `test_start_timer_empty_actor_uses_default` — _CSA-1_
- [x] Velasari writes `test_concurrent_timers_different_actors` — _CSA-5_
- [x] Velasari writes `test_stop_timer_with_explicit_actor` — _CSA-2_
- [x] Velasari writes `test_start_node_with_actor` — _CSA-3_
- [x] Velasari writes `test_complete_node_with_actor` — _CSA-3_
- [x] Velasari writes `test_get_active_timer_with_actor` — _CSA-4_
- [x] Velasari runs full test suite to confirm all tests pass — _CSA-1, CSA-2, CSA-3, CSA-4, CSA-5_
