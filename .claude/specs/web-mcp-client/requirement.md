# Web Backend MCP Client Refactoring - Requirements

## Overview

Refactor the web backend to communicate with Taskyn core via MCP protocol using streamable HTTP transport, replacing the current direct in-process function invocation pattern.

## User Stories

### US-1: Decoupled Architecture
**As a** system architect
**I want** the web backend to communicate with Taskyn MCP server over HTTP
**So that** I can deploy them as separate containers and scale independently

**Acceptance Criteria:**
- Web backend uses FastMCP/httpx client to call MCP tools
- No direct Python imports from `taskyn.mcp.server` module
- Communication happens over streamable HTTP transport
- Each component can be started/stopped independently

---

### US-2: Configuration-Driven MCP Endpoint
**As a** DevOps engineer
**I want** the MCP server URL to be configurable via environment variables
**So that** I can easily configure different environments (dev, staging, prod)

**Acceptance Criteria:**
- `TASKYN_MCP_URL` environment variable controls the MCP server endpoint
- Default value: `http://localhost:8000`
- Configuration is validated at startup
- Clear error message if MCP server is unreachable

---

### US-3: Async HTTP Communication
**As a** developer
**I want** all MCP tool calls to use async HTTP client
**So that** the FastAPI backend maintains its async nature without blocking

**Acceptance Criteria:**
- Uses `httpx.AsyncClient` for HTTP communication
- Properly manages client lifecycle (connection pooling)
- Supports concurrent tool calls where appropriate
- No sync-over-async anti-patterns

---

### US-4: Robust Error Handling
**As a** user
**I want** meaningful error messages when MCP communication fails
**So that** I can understand and troubleshoot issues

**Acceptance Criteria:**
- Network errors mapped to appropriate HTTP status codes (502, 503, 504)
- MCP tool errors (NotFound, Validation, etc.) mapped correctly (404, 422)
- Timeout handling with configurable timeouts
- Retry logic for transient failures (optional, configurable)

---

### US-5: Session Management
**As a** system
**I want** proper MCP session handling
**So that** the server can maintain context across requests if needed

**Acceptance Criteria:**
- Captures `Mcp-Session-Id` from server responses
- Sends session ID in subsequent requests
- Handles session expiry gracefully

---

### US-6: Health Check Integration
**As a** DevOps engineer
**I want** the web backend health check to verify MCP server connectivity
**So that** I can monitor system health holistically

**Acceptance Criteria:**
- `/health` endpoint includes MCP server status
- Reports degraded state if MCP server unreachable
- Does not block startup if MCP server is temporarily unavailable

---

### US-7: Docker Deployment Support
**As a** DevOps engineer
**I want** Docker Compose configuration for two-container deployment
**So that** I can deploy web backend and MCP server as separate services

**Acceptance Criteria:**
- `docker-compose.yml` defines two services: `web` and `mcp`
- Services can communicate via Docker network
- Environment variables properly configured
- Health checks for both services

---

## Non-Functional Requirements

### NFR-1: Performance
- HTTP overhead should be acceptable for typical PM operations
- Connection pooling to minimize connection setup latency
- Consider batching for bulk operations

### NFR-2: Reliability
- Graceful degradation if MCP server is temporarily unavailable
- Clear logging for debugging communication issues

### NFR-3: Security
- Support for future authentication between services (out of scope for initial implementation)
- No sensitive data logged

### NFR-4: Backward Compatibility
- All existing API endpoints must continue to work
- No changes to frontend required
