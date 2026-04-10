# Windows Startup Setup for Taskyn

**Date**: 2026-03-31
**Updated**: 2026-03-31 — corrected to always-HTTP, cognitive-memory pattern
**Scope**: Research + implementation plan

---

## 1. Runtime Components

Taskyn always runs as **streamable HTTP** — never stdio. The SQLite DB cannot be shared between multiple processes, so a single persistent HTTP server is the only correct mode.

| Component | Port | Command | Auto-start |
|-----------|------|---------|------------|
| **MCP Server** | 8020 | `python -m taskyn.mcp --transport streamable-http --host 127.0.0.1 --port 8020` | **Yes** |
| **Web UI** | 3020 | `uvicorn taskyn.web.backend.main:app --host 0.0.0.0 --port 3020` | **Yes** — depends on MCP being up |
| CLI | — | `taskyn` | No — on demand |
| Dev server | — | `python scripts/dev_server.py` | No — dev only |

Environment variables:
- `TASKYN_DB` — path to SQLite database (should be `~/.taskyn/data/taskyn.db`)
- `TASKYN_MCP_HOST` / `TASKYN_MCP_PORT` — bind address and port
- `TASKYN_MCP_URL` — Web UI uses this to connect to MCP server
- `TASKYN_JWT_SECRET` — Web UI auth secret
- `TASKYN_ACTOR` — audit log actor ID

---

## 2. Approach: Task Scheduler (same as cognitive-memory)

Follow the exact pattern from `C:/Projects/cognitive-memory/src/cognitive_memory/service.py`:

- **Windows Task Scheduler** with `AtLogOn` trigger
- **`pythonw.exe`** (windowless) so no console window appears
- **Restart on failure**: 3 retries, 1 minute apart
- **No time limit** on execution
- **CLI management**: `install`, `remove`, `start`, `stop`, `status`
- **Fallback**: Startup folder `.bat` if Task Scheduler is denied

### Key differences from cognitive-memory:

| | Cognitive Memory | Taskyn |
|---|---|---|
| Tasks | 1 (single server) | 2 (MCP server + Web UI) |
| DB location | `~/.cognitive-memory/data/` | `~/.taskyn/data/taskyn.db` |
| Port | 8050 | 8020 (MCP), 3020 (Web) |
| Task name | `CognitiveMemory` | `TaskynMCP`, `TaskynWeb` |
| Dependency | None | Web UI waits for MCP server |

---

## 3. Implementation Plan

### 3.1 Create `service.py` in Taskyn

Add `src/taskyn/service.py` modeled on cognitive-memory's `service.py` with:

```python
TASK_NAME_MCP = "TaskynMCP"
TASK_NAME_WEB = "TaskynWeb"
LOG_DIR = Path.home() / ".taskyn"
LOG_FILE = LOG_DIR / "service.log"
```

**Two scheduled tasks:**

1. **TaskynMCP** — starts MCP server with `pythonw.exe -m taskyn.mcp --transport streamable-http`
2. **TaskynWeb** — starts Web UI with `pythonw.exe -m uvicorn taskyn.web.backend.main:app --host 0.0.0.0 --port 3020`
   - Uses `AtLogOn` trigger with 15-second delay (`PT15S`)
   - Plus a readiness poll in the startup to wait for MCP

**Environment setup in the task action:**
```python
# Set env vars before launch
env_setup = (
    f"$env:TASKYN_DB='{Path.home() / '.taskyn' / 'data' / 'taskyn.db'}'; "
    f"$env:TASKYN_MCP_URL='http://127.0.0.1:8020/mcp'; "
)
```

### 3.2 CLI entrypoint

Add to `pyproject.toml`:
```toml
[project.scripts]
taskyn-service = "taskyn.service:handle_command_line"
```

Usage:
```
taskyn-service install    # Install both tasks (MCP + Web)
taskyn-service remove     # Remove both tasks
taskyn-service start      # Start both now
taskyn-service stop       # Stop both
taskyn-service status     # Show status of both + port checks
```

### 3.3 Data directory

Ensure `~/.taskyn/data/` exists on install. Store:
- `taskyn.db` — main database
- `users.db` — web UI auth database
- `service.log` — combined log output

---

## 4. Claude Code MCP Config

Since Taskyn always runs as HTTP, Claude Code connects via HTTP (not stdio):

```json
{
  "mcpServers": {
    "taskyn": {
      "type": "http",
      "url": "http://127.0.0.1:8020/mcp"
    }
  }
}
```

This is already how it's configured. The Task Scheduler ensures the server is running before Claude Code starts.

---

## 5. Startup Order

```
Windows Login
    │
    ├── Task Scheduler: TaskynMCP (immediate)
    │       └── pythonw.exe -m taskyn.mcp --transport streamable-http
    │           └── Listening on :8020
    │
    ├── Task Scheduler: TaskynWeb (15s delay)
    │       └── Poll :8020 until ready
    │       └── pythonw.exe -m uvicorn taskyn.web.backend.main:app
    │           └── Listening on :3020
    │
    ├── Task Scheduler: CognitiveMemory (existing)
    │       └── Listening on :8050
    │
    └── User starts Claude Code
            └── Connects to :8020 (Taskyn), :8050 (CogMem), :8060 (WorkerMgr)
```
