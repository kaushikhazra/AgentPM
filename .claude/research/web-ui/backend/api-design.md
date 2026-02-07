# API Design

This document defines the FastAPI REST API design for Taskyn's web interface.

---

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  React UI   │ ───► │  FastAPI    │ ───► │ MCP Server  │ ───► │ Taskyn Core │
│  (Browser)  │ HTTP │  (REST)     │      │ (Tools)     │      │ (Python)    │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
```

**Key Principle**: FastAPI calls MCP tools. No business logic in FastAPI layer.

---

## Base URL & Versioning

```
Base URL: /api/v1
```

All endpoints are prefixed with `/api/v1` for versioning.

---

## Endpoint Design

All endpoints map 1:1 to MCP tools. FastAPI is a thin REST-to-MCP bridge.

### Companies

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/companies` | List all companies | `pm_list_companies` |
| GET | `/companies/:id` | Get company by ID | `pm_get_company` |
| POST | `/companies` | Create company | `pm_create_company` |
| DELETE | `/companies/:id` | Delete company | `pm_delete_company` |

### Projects

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/projects` | List projects (with filters) | `pm_list_projects` |
| GET | `/projects/:id` | Get project by ID | `pm_get_project` |
| POST | `/projects` | Create project | `pm_create_project` |
| PATCH | `/projects/:id` | Update project | `pm_update_project` |
| DELETE | `/projects/:id` | Delete project | `pm_delete_project` |
| GET | `/projects/:id/methodology` | Get methodology info | `pm_get_methodology_info` |
| GET | `/projects/:id/stats` | Get project stats | `pm_get_project_stats` |

**Query Parameters:**
- `company_id` - Filter by company
- `status` - Filter by status (active, archived)

### Nodes (Generic)

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/nodes` | List nodes (with filters) | `pm_list_nodes` |
| GET | `/nodes/:id` | Get node by ID | `pm_get_node` |
| POST | `/nodes` | Create node | `pm_create_node` |
| PATCH | `/nodes/:id` | Update node | `pm_update_node` |
| POST | `/nodes/:id/start` | Transition to in_progress | `pm_start_node` |
| POST | `/nodes/:id/complete` | Transition to done | `pm_complete_node` |
| POST | `/nodes/:id/block` | Mark as blocked | `pm_block_node` |
| GET | `/nodes/:id/ancestors` | Get ancestor chain | `pm_get_ancestors` |
| GET | `/nodes/:id/descendants` | Get descendant tree | `pm_get_descendants` |
| GET | `/nodes/:id/rollup` | Get aggregated stats | `pm_get_rollup` |

**Query Parameters:**
- `project_id` - Filter by project
- `node_type` - Filter by type (epic, story, task, spec, etc.)
- `status` - Filter by status
- `assignee` - Filter by assignee

### Milestones

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/milestones` | List milestones | `pm_list_milestones` |
| POST | `/milestones` | Create milestone | `pm_create_milestone` |
| POST | `/milestones/:id/complete` | Complete milestone | `pm_complete_milestone` |

**Query Parameters:**
- `project_id` - Filter by project (required)
- `status` - Filter by status

### Edges

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/edges` | List edges (with filters) | `pm_list_edges` |
| POST | `/edges` | Create edge | `pm_create_edge` |
| DELETE | `/edges/:id` | Delete edge | `pm_delete_edge` |

**Query Parameters:**
- `project_id` - Filter by project
- `source_id` - Filter by source node
- `target_id` - Filter by target node
- `edge_type` - Filter by type (parent, depends_on, etc.)

### Time Tracking

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| POST | `/timer/start` | Start timer on node | `pm_start_timer` |
| POST | `/timer/stop` | Stop active timer | `pm_stop_timer` |
| GET | `/timer/current` | Get active timer state | `pm_get_active_timer` |
| POST | `/time-entries` | Log time manually | `pm_log_time` |

### Tags

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/tags` | List all tags | `pm_list_tags` |
| POST | `/tags` | Create tag | `pm_create_tag` |
| POST | `/nodes/:id/tags` | Tag a node | `pm_tag_node` |
| DELETE | `/nodes/:id/tags/:name` | Untag a node | `pm_untag_node` |

### Reporting & Activity

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/dashboard` | Dashboard aggregates | `pm_get_dashboard` |
| GET | `/activity` | Recent activity log | `pm_get_recent_activity` |
| GET | `/search` | Full-text search | `pm_search` |

**Activity Query Parameters:**
- `entity_type` - Filter by entity (node, project, etc.)
- `entity_id` - Filter by entity ID
- `limit` - Max entries to return

**Search Query Parameters:**
- `query` - Search text (required)
- `entity_type` - Filter by entity type
- `project_id` - Filter by project
- `limit` - Max results (default: 20)

---

## Request/Response Schemas

### Node Schemas

```python
# schemas/nodes.py
from pydantic import BaseModel
from datetime import datetime

class NodeCreate(BaseModel):
    project_id: str
    node_type: str
    title: str
    description: str | None = None
    status: str | None = None  # Uses methodology default if not provided
    parent_id: str | None = None  # Creates parent edge if provided
    properties: dict | None = None

class NodeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    properties: dict | None = None

class NodeResponse(BaseModel):
    id: str
    project_id: str
    node_type: str
    title: str
    description: str | None
    status: str
    properties: dict | None
    created_at: datetime
    updated_at: datetime

class NodeWithChildren(NodeResponse):
    children: list[NodeResponse]
    child_count: int
```

### Project Schemas

```python
# schemas/projects.py
class ProjectCreate(BaseModel):
    name: str
    company_id: str | None = None
    methodology: str = "classic_agile"
    description: str | None = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    company_id: str | None
    methodology: str
    description: str | None
    created_at: datetime
    updated_at: datetime
```

### Error Response

```python
# schemas/common.py
class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None  # e.g., "NOT_FOUND", "VALIDATION_ERROR"
```

---

## Error Handling

### HTTP Status Codes

| Status | When |
|--------|------|
| 200 | Success (GET, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (no/invalid token) |
| 403 | Forbidden (valid token, no permission) |
| 404 | Not Found |
| 409 | Conflict (duplicate, constraint violation) |
| 422 | Unprocessable Entity (business rule violation) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": "Node not found",
  "detail": "No node with ID 'abc123' exists",
  "code": "NOT_FOUND"
}
```

### Exception Mapping

MCP tool errors are mapped to HTTP status codes via the `call_mcp_tool` helper
in `deps.py` (see MCP Integration section above). FastAPI never imports from
`taskyn.exceptions` directly - all errors flow through MCP.

---

## FastAPI Implementation

### Main App Setup

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Taskyn API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3020"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(nodes_router, prefix="/api/v1")
app.include_router(edges_router, prefix="/api/v1")
app.include_router(time_entries_router, prefix="/api/v1")
app.include_router(timer_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
```

### Example Router

```python
# routes/nodes.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/nodes", tags=["nodes"])

@router.get("/{node_id}")
async def get_node_endpoint(
    node_id: str,
    mcp = Depends(get_mcp),
    current_user: User = Depends(get_current_user),
):
    result = await mcp.call_tool("pm_get_node", {"node_id": node_id})
    return result

@router.post("/", status_code=201)
async def create_node_endpoint(
    data: NodeCreate,
    mcp = Depends(get_mcp),
    current_user: User = Depends(get_current_user),
):
    result = await mcp.call_tool("pm_create_node", {
        "project_id": data.project_id,
        "node_type": data.node_type,
        "title": data.title,
        "description": data.description,
        "assignee": data.assignee,
        "priority": data.priority,
        "parent_id": data.parent_id,
    })
    return result

@router.post("/{node_id}/start")
async def start_node_endpoint(
    node_id: str,
    mcp = Depends(get_mcp),
    current_user: User = Depends(get_current_user),
):
    result = await mcp.call_tool("pm_start_node", {"node_id": node_id})
    return result
```

---

## MCP Integration

**Core Principle**: MCP is the single entry point to Taskyn core. FastAPI never
imports from `taskyn.core`, `taskyn.graph`, or `taskyn.db`. It only talks to
the MCP server.

FastAPI uses the MCP server instance in-process via `call_tool()`:

```python
# deps.py
from taskyn.mcp.server import mcp as mcp_server

async def get_mcp():
    """Dependency that provides the MCP server instance."""
    return mcp_server
```

### How It Works

```
FastAPI Route
  → mcp.call_tool("pm_create_node", {...})
    → MCP tool function executes
      → Taskyn core logic runs
        → Returns result
  → FastAPI serializes to JSON response
```

### Why MCP as the Single Entry Point?

Taskyn is an **AI-first** project management tool. MCP is the interface where
LLMs and AI agents connect. When a human creates a task via the Web UI and an
AI agent creates a task via MCP, they must go through the exact same code path.
One set of validation, one set of business logic, one set of activity logging -
no divergence possible.

| Approach | DRY | Consistency | Validation |
|----------|-----|-------------|------------|
| FastAPI → Core (direct) | Violates DRY - two paths to core | AI agents via MCP may behave differently from Web | Must duplicate MCP's validation |
| FastAPI → MCP → Core | Single path | Humans and AI agents behave identically | MCP handles all validation |

### Error Handling from MCP

MCP tools raise `ValueError` on failure. FastAPI catches and maps to HTTP:

```python
# deps.py
from fastapi import HTTPException

async def call_mcp_tool(mcp, tool_name: str, args: dict):
    """Call an MCP tool and map errors to HTTP responses."""
    try:
        return await mcp.call_tool(tool_name, args)
    except ValueError as e:
        msg = str(e).lower()
        if "not found" in msg:
            raise HTTPException(404, detail=str(e))
        if "already exists" in msg or "cycle" in msg:
            raise HTTPException(409, detail=str(e))
        raise HTTPException(422, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail="Internal server error")
```

---

## React API Client

### Client Setup

```typescript
// src/api/client.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('token');

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new ApiError(error.error, error.detail, error.code, res.status);
  }

  if (res.status === 204) return null as T;
  return res.json();
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),
};
```

### Resource APIs

```typescript
// src/api/nodes.ts
import { api } from './client';
import type { Node, NodeCreate, NodeUpdate } from '@/types';

export const nodesApi = {
  list: (projectId: string, filters?: { nodeType?: string; status?: string }) =>
    api.get<Node[]>(`/nodes?project_id=${projectId}&${new URLSearchParams(filters)}`),

  get: (id: string) => api.get<Node>(`/nodes/${id}`),

  create: (data: NodeCreate) => api.post<Node>('/nodes', data),

  update: (id: string, data: NodeUpdate) => api.patch<Node>(`/nodes/${id}`, data),

  delete: (id: string) => api.delete(`/nodes/${id}`),

  getChildren: (id: string) => api.get<Node[]>(`/nodes/${id}/children`),

  getAncestors: (id: string) => api.get<Node[]>(`/nodes/${id}/ancestors`),
};
```

---

## Decisions

- [x] **RESTful design** - Standard CRUD endpoints
- [x] **Generic `/nodes` endpoint** - Works for all node types
- [x] **MCP as single entry point** - FastAPI calls MCP tools, never imports core directly
- [x] **Thin bridge pattern** - FastAPI only handles HTTP concerns (auth, serialization, status codes)
- [x] **Pydantic schemas** - Request/response validation at the HTTP boundary
- [x] **Standard error format** - Consistent error responses
- [x] **CORS configured** - For React dev server

---

## Summary

```
/api/v1/
├── /auth/*           → Authentication (see auth-flow.md)
├── /companies/*      → Company CRUD
├── /projects/*       → Project CRUD
├── /nodes/*          → Node CRUD (generic, all types)
├── /edges/*          → Edge CRUD
├── /time-entries/*   → Time entry CRUD
├── /timer/*          → Active timer control
├── /activity         → Activity log
├── /dashboard        → Dashboard aggregates
└── /methodologies/*  → Methodology metadata
```

