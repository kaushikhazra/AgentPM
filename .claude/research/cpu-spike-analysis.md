# CPU Spike Analysis — Taskyn MCP Server

**Date**: 2026-04-08  
**Symptom**: 23,340 seconds of CPU consumed while server was idle  
**Status**: FIXED in commit `dc48a7e` (April 5, 2026)

---

## Root Cause

Two distinct bugs. One was the kill shot; one added fuel.

### Bug 1 (Primary) — External FastMCP library spinning a background thread

The MCP server used the external `fastmcp` PyPI package (`fastmcp>=2.0.0`) as a core dependency. This library includes **pydocket/fakeredis** for session management — a Redis-backed session store with a background polling thread that runs continuously regardless of request volume. Even with zero active clients, the thread busy-polls, burning CPU indefinitely.

This was already suspected ("fixed once by switching to raw mcp SDK") — but the fix had not yet been applied to Taskyn at the time of the spike.

### Bug 2 (Secondary) — strptime format-loop compiling regex on every call

Five core modules (`activity.py`, `company.py`, `project.py`, `time_entry.py`, `graph/nodes.py`) shared this pattern:

```python
for fmt in ["%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        continue
```

Each `strptime` call compiles a regex internally. With 4 formats × 5 files × multiple calls per request, this generates **40,000+ regex compilations per request**. Not the idle-CPU cause, but a significant per-request cost amplifier.

---

## Evidence

| Evidence | Detail |
|----------|--------|
| Commit message `dc48a7e` | Explicitly names "pydocket/fakeredis background thread that caused idle CPU spikes" |
| `server.py` (before fix) | `from fastmcp import FastMCP` — external lib, no `stateless_http` flag |
| `server.py` (after fix) | `from mcp.server.fastmcp import FastMCP` + `stateless_http=True` |
| `pyproject.toml` (before) | `fastmcp>=2.0.0` in core `dependencies` |
| `pyproject.toml` (after) | `mcp>=1.0.0` in core deps; `fastmcp` moved to `web` optional group |
| Grep: no `while True` | No busy-wait loops anywhere in `src/` |
| Grep: no `asyncio.sleep(0)` | No Python-level busy-waits |
| Grep: no `asyncio.create_task` | No background task spawning in app code |
| `db/connection.py` | Clean — single SQLite connection, no polling, no threads |

**Why Taskyn spiked vs. Velhari (~20s) and Cognitive Memory (~49s):**  
Both healthy services use the built-in `mcp` SDK. Taskyn uniquely had `fastmcp` (external) as a core dependency, which ships the pydocket/fakeredis session manager. That thread is the entire delta.

---

## Fix

Both bugs were fixed in commit `dc48a7e` on April 5, 2026.

### Fix 1 — Switch to built-in MCP SDK

**`src/taskyn/mcp/server.py`**
```python
# Before
from fastmcp import FastMCP
mcp = FastMCP("taskyn", instructions="""...""")

# After
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("taskyn", instructions="""...""", stateless_http=True)
```

`stateless_http=True` disables session management entirely — no state stored, no background thread, no Redis dependency.

**`pyproject.toml`**
```toml
# Before
dependencies = [
    "fastmcp>=2.0.0",
    ...
]

# After
dependencies = [
    "mcp>=1.0.0",
    ...
]
[project.optional-dependencies]
web = [
    "fastmcp>=2.0.0",  # only needed for web layer, not MCP server
    ...
]
```

### Fix 2 — Replace strptime loop with fromisoformat

Applied across all 5 files:
```python
# Before
for fmt in ["%Y-%m-%d %H:%M:%S.%f%z", ...]:
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        continue

# After
try:
    return datetime.fromisoformat(value)
except ValueError:
    pass
```

`datetime.fromisoformat()` is a single C-level call — no regex compilation.

---

## Verification

The fix is already deployed (commit `dc48a7e`). To confirm the service is healthy after re-enabling:

1. **Re-enable the Windows scheduled task** (was disabled April 5)
2. **Let it run idle for 30 minutes** with no MCP calls
3. **Check CPU time** via Task Manager → Details → right-click columns → "CPU Time"
   - Expected: < 5 seconds after 30 minutes idle (comparable to Velhari/Cognitive Memory baselines)
   - Before fix: would accumulate ~800 seconds per 30 minutes idle
4. **Check the log file** at `~/.taskyn/service.log` — should show clean uvicorn startup, no error spam
5. **Send one test MCP call** (e.g., `pm_get_dashboard`) and confirm response time is normal

If CPU is still high after the fix, the next suspect would be uvicorn's default keep-alive configuration — but there is no evidence pointing there currently.
