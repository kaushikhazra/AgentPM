# Caller-Scoped Actor for Timer/Workflow — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Add optional `actor` param to 5 MCP tools, resolve via `actor or get_actor()` | Minimal change. Core layer already accepts `actor` — only the MCP shim needs the override. Backward compatible: omitting `actor` preserves current behavior (CSA-1 through CSA-4). |
| D2 | Normalize empty string to transport default, not to `None` | `actor=""` should mean "I didn't pass an actor" → fall back to `get_actor()`. This differs from core layer D9 which normalizes `""` to `None`. At the MCP layer, empty means "use default", not "use NULL actor". |
| D3 | No changes to core layer, models, schema, CLI, or frontend | The core already handles arbitrary actor strings. This spec is purely an MCP tool layer change + tests (CSA requirements, infrastructure dependencies table). |
| D4 | Extract `_resolve_actor(actor)` helper to centralize resolution | Five tools need the same `actor or get_actor()` logic. A one-liner helper prevents inconsistency and makes the resolution rule explicit. |

---

## 1. Actor Resolution Helper

Add a helper function alongside `get_actor()` in `mcp/server.py`:

```python
def _resolve_actor(actor: str | None) -> str:
    """Resolve caller-provided actor or fall back to transport default.

    - Non-empty string: use as-is (caller override)
    - None or empty string: fall back to get_actor() (transport default)
    """
    return actor if actor else get_actor()
```

**Resolution table:**

| Caller passes | `_resolve_actor()` returns | Why |
|--------------|--------------------------|-----|
| `actor="sub-1"` | `"sub-1"` | Caller override (CSA-1) |
| `actor=None` | `get_actor()` → e.g. `"web"` | Backward compat — no param passed |
| `actor=""` | `get_actor()` → e.g. `"web"` | Empty string = not provided (D2) |
| _(param omitted)_ | `get_actor()` → e.g. `"web"` | Default value is `None` → same as above |

_Traces to: CSA-1, CSA-2, CSA-3, CSA-4_

---

## 2. MCP Tool Signature Changes

Five tools gain an optional `actor: str | None = None` parameter. Each tool's internal call changes from `actor=get_actor()` to `actor=_resolve_actor(actor)`.

### 2.1 `pm_start_timer`

```python
@mcp.tool()
def pm_start_timer(node_id: str, notes: str | None = None, actor: str | None = None) -> dict:
    """
    Start a timer on a node (timer-only, no status change).

    This is a pure time-tracking operation that does NOT change the node's status.
    If another timer is running for this actor, it will be automatically stopped.

    Use pm_start_node instead if you want to both change status AND start timing.

    Args:
        node_id: Node to track time on
        notes: Optional notes about the work
        actor: Optional actor identity override. If omitted, uses the server's default actor.

    Returns:
        The created time entry object
    """
    from taskyn.core import start_timer
    entry = start_timer(node_id, notes=notes, actor=_resolve_actor(actor))
    return entry.model_dump()
```

_Traces to: CSA-1_

### 2.2 `pm_stop_timer`

```python
@mcp.tool()
def pm_stop_timer(entry_id: str | None = None, actor: str | None = None) -> dict | None:
    """
    Stop a running timer.

    If no entry_id provided, stops the currently active timer for this actor.

    Args:
        entry_id: Optional - stop specific time entry (ignores actor)
        actor: Optional actor identity override. If omitted, uses the server's default actor.

    Returns:
        The stopped time entry, or None if no timer was running
    """
    from taskyn.core import stop_timer
    entry = stop_timer(entry_id=entry_id, actor=_resolve_actor(actor))
    return entry.model_dump() if entry else None
```

_Traces to: CSA-2_

### 2.3 `pm_start_node`

```python
@mcp.tool()
def pm_start_node(node_id: str, actor: str | None = None) -> dict:
    """
    Start working on a node (workflow action).

    This is a workflow action that:
    1. Changes the node's status to in_progress
    2. Automatically starts a timer for this actor

    Use this when beginning work on a task. For timer-only operations,
    use pm_start_timer instead.

    Args:
        node_id: Node ID
        actor: Optional actor identity override. If omitted, uses the server's default actor.

    Returns:
        The updated node object
    """
    from taskyn.core import start_node
    node = start_node(node_id, actor=_resolve_actor(actor))
    return node.model_dump()
```

_Traces to: CSA-3_

### 2.4 `pm_complete_node`

```python
@mcp.tool()
def pm_complete_node(node_id: str, actor: str | None = None) -> dict:
    """
    Complete a node.

    Stops any active timer for this actor and sets status to done.

    Args:
        node_id: Node ID
        actor: Optional actor identity override. If omitted, uses the server's default actor.

    Returns:
        The updated node object
    """
    from taskyn.core import complete_node
    node = complete_node(node_id, actor=_resolve_actor(actor))
    return node.model_dump()
```

_Traces to: CSA-3_

### 2.5 `pm_get_active_timer`

```python
@mcp.tool()
def pm_get_active_timer(actor: str | None = None) -> dict | None:
    """
    Get the currently active timer for this actor.

    Args:
        actor: Optional actor identity override. If omitted, uses the server's default actor.

    Returns:
        Active time entry with node info, or None
    """
    from taskyn.core import get_active_timer
    from taskyn.graph import get_node

    entry = get_active_timer(actor=_resolve_actor(actor))
    if not entry:
        return None

    node = get_node(entry.node_id)
    return {
        **entry.model_dump(),
        "node_title": node.title if node else None,
        "node": node.model_dump() if node else None,
    }
```

_Traces to: CSA-4_

### 2.6 `pm_get_active_timers` — No change

Already returns all timers across all actors. No actor parameter needed.

---

## 3. Test Strategy

### 3.1 Existing tests — no changes expected

All existing tests pass `actor=None` or use `get_actor()` defaults. The `_resolve_actor(None)` path returns `get_actor()`, identical to current behavior.

### 3.2 New test: MCP tool layer actor override

A new test file `tests/test_mcp_actor_override.py` (or added to existing MCP tests) that validates the MCP tool layer specifically:

| Test | What it validates |
|------|-------------------|
| `test_start_timer_with_explicit_actor` | `pm_start_timer(node, actor="sub-1")` creates entry with `actor="sub-1"` |
| `test_start_timer_no_actor_uses_default` | `pm_start_timer(node)` creates entry with `actor=get_actor()` |
| `test_start_timer_empty_actor_uses_default` | `pm_start_timer(node, actor="")` creates entry with `actor=get_actor()` |
| `test_concurrent_timers_different_actors` | `pm_start_timer(A, actor="sub-1")` then `pm_start_timer(B, actor="sub-2")` — both active via `pm_get_active_timers()` (CSA-5) |
| `test_stop_timer_with_explicit_actor` | Two actors running. `pm_stop_timer(actor="sub-1")` stops only sub-1's timer. |
| `test_start_node_with_actor` | `pm_start_node(node, actor="sub-1")` starts timer under `"sub-1"` |
| `test_complete_node_with_actor` | `pm_complete_node(node, actor="sub-1")` stops only `"sub-1"`'s timer |
| `test_get_active_timer_with_actor` | `pm_get_active_timer(actor="sub-1")` returns only sub-1's timer |

Tests call core functions directly (not via MCP protocol) since `_resolve_actor` is the unit under test. Import the MCP tool functions and call them, or test `_resolve_actor` directly.

---

## Files Changed

| File | Change |
|------|--------|
| `src/taskyn/mcp/server.py` | Add `_resolve_actor()` helper; add `actor: str \| None = None` param to 5 tools; update docstrings |
| `tests/test_mcp_actor_override.py` | New test file for actor override behavior (8 test cases) |

---

## Future Work (Out of Scope)

- **Actor parameter on `pm_log_time`** — could be added for manual time logging, but not requested in CSA requirements.
- **Actor parameter on `pm_block_node`** — workflow action that doesn't involve timers, no need.
- **MCP server instructions update** — documenting the actor parameter in the server's system instructions for LLM callers. Deferred.
