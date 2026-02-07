# Web Backend MCP Client Refactoring - Tasks

## Phase 1: Update Dependencies

- [x] Update `src/taskyn/web/backend/deps.py`
  - [x] Replace direct imports with `from fastmcp import Client`
  - [x] Add `get_mcp_settings()` configuration function
  - [x] Add `init_mcp_client()` using `Client(url)`
  - [x] Add `close_mcp_client()` lifecycle function
  - [x] Add `get_mcp_client()` dependency
  - [x] Refactor `call_mcp_tool()` to use FastMCP Client
  - [x] Extract `.data` from `CallToolResult`
  - [x] Map `ClientError` to HTTP status codes
  - [x] Remove `_get_tool_func()` helper
  - [x] Remove `from taskyn.mcp.server import mcp`
  _US-1, US-2, US-4_

- [x] Update `src/taskyn/web/backend/main.py`
  - [x] Add lifespan context manager
  - [x] Call `init_mcp_client()` on startup
  - [x] Call `close_mcp_client()` on shutdown
  - [x] Update FastAPI app to use lifespan
  _US-1_

## Phase 2: Update Routes (add `await`)

- [x] Update `src/taskyn/web/backend/routes/companies.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/projects.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/nodes.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/edges.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/milestones.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/tags.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/timer.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/time_entries.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/dashboard.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/activity.py`
  _US-1, US-3_

- [x] Update `src/taskyn/web/backend/routes/search.py`
  _US-1, US-3_

## Phase 3: Health Check

- [x] Add health check endpoint
  - [x] Create `/health` endpoint
  - [x] Use `client.list_tools()` as connectivity check
  - [x] Return degraded status if MCP unreachable
  _US-6_

## Phase 4: Integration Testing

- [x] Create `tests/test_mcp_integration.py`
  - [x] Test full flow: API → FastMCP Client → MCP Server
  - [x] Test error scenarios (MCP server down, timeout)
  - [x] Test concurrent requests
  _US-1, US-3, US-4_

- [x] Update existing route tests
  - [x] Use FastMCP Client in-memory transport for tests
  _US-1_

## Phase 5: Docker Configuration

- [x] Create `Dockerfile.mcp`
  - [x] Base Python image
  - [x] Install taskyn package
  - [x] Expose port 8000
  - [x] CMD: `python -m taskyn.mcp --transport streamable-http`
  _US-7_

- [x] Create `Dockerfile.web`
  - [x] Base Python image
  - [x] Install taskyn[web] package
  - [x] Build frontend assets
  - [x] Expose port 3020
  - [x] CMD: uvicorn
  _US-7_

- [x] Create `docker-compose.yml`
  - [x] Define `mcp` service with health check
  - [x] Define `web` service dependent on mcp
  - [x] Configure shared volume for database
  - [x] Configure `TASKYN_MCP_URL` environment variable
  _US-7_

- [x] Test Docker deployment
  - [x] Verify two-container communication
  - [x] Test health checks
  - [x] Test restart scenarios
  _US-7_

## Phase 6: Documentation

- [x] Update project README
  - [x] Document `TASKYN_MCP_URL` environment variable
  - [x] Document Docker deployment steps
  _US-2, US-7_
