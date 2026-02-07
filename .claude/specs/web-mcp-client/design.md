# Web Backend MCP Client Refactoring - Design

## Current Architecture (Problem)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINGLE PROCESS (Monolithic)                  │
│                                                                  │
│  ┌─────────────┐    direct import    ┌──────────────────────┐  │
│  │  FastAPI    │ ──────────────────► │  MCP Server Module   │  │
│  │  Backend    │    getattr(.fn)     │  (taskyn.mcp.server) │  │
│  │             │ ◄────────────────── │                      │  │
│  └─────────────┘    Python call      └──────────────────────┘  │
│         │                                      │                │
│         └──────────────┬───────────────────────┘                │
│                        ▼                                        │
│              ┌──────────────────┐                               │
│              │  Taskyn Core     │                               │
│              │  + SQLite DB     │                               │
│              └──────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

**Problems:**
1. Tight coupling - can't deploy separately
2. Single point of failure
3. Can't scale components independently
4. Violates Dependency Inversion Principle

---

## Target Architecture (Solution)

```
┌─────────────────────────┐         ┌─────────────────────────────┐
│     Container A         │         │       Container B           │
│                         │         │                             │
│  ┌─────────────────┐    │  HTTP   │  ┌───────────────────────┐  │
│  │   FastAPI       │    │ ──────► │  │   Taskyn MCP Server   │  │
│  │   Web Backend   │    │ (MCP)   │  │   (streamable-http)   │  │
│  │                 │    │ ◄────── │  │                       │  │
│  │  ┌───────────┐  │    │         │  └───────────┬───────────┘  │
│  │  │ MCP Client│  │    │         │              │              │
│  │  │ (httpx)   │  │    │         │              ▼              │
│  │  └───────────┘  │    │         │  ┌───────────────────────┐  │
│  └─────────────────┘    │         │  │   Taskyn Core         │  │
│                         │         │  │   + SQLite DB         │  │
│  ┌─────────────────┐    │         │  └───────────────────────┘  │
│  │   Frontend      │    │         │                             │
│  │   (static)      │    │         │                             │
│  └─────────────────┘    │         │                             │
└─────────────────────────┘         └─────────────────────────────┘
```

**Benefits:**
1. True microservices architecture
2. Independent scaling
3. Separate failure domains
4. Clean dependency boundaries
5. AI agents and Web UI use same interface (MCP protocol)

---

## Component Design

### 1. MCP Client - Using FastMCP Client Library

**Reference:** [FastMCP Client Documentation](https://gofastmcp.com/clients/client)

**No custom client needed.** FastMCP provides a built-in `Client` class that handles:
- HTTP transport (auto-detected from URL)
- JSON-RPC protocol
- SSE response parsing
- Session management
- Connection lifecycle

**Usage:**

```python
from fastmcp import Client

# FastMCP auto-detects HTTP transport from URL
client = Client("http://localhost:8000/mcp")

async with client:
    # List available tools
    tools = await client.list_tools()

    # Call a tool
    result = await client.call_tool("pm_list_companies", {})
    print(result.data)
```

**Key Points:**
- Pass URL string → FastMCP uses HTTP transport
- Pass FastMCP server instance → FastMCP uses in-memory transport (for testing)
- Pass file path → FastMCP uses stdio transport (subprocess)

**No custom `mcp_client.py` file needed.** We use FastMCP directly.

---

### 2. Dependency Injection Updates

**Location:** `src/taskyn/web/backend/deps.py`

```python
"""
Dependencies for FastAPI routes.
Refactored to use FastMCP Client over HTTP.
"""

import os
from typing import Annotated
from functools import lru_cache

from fastapi import Depends, HTTPException
from fastmcp import Client
from fastmcp.exceptions import ClientError


# Configuration
@lru_cache
def get_mcp_settings():
    url = os.environ.get("TASKYN_MCP_URL")
    if not url:
        raise RuntimeError("TASKYN_MCP_URL environment variable is required")
    return {
        "url": url,
        "timeout": float(os.environ.get("TASKYN_MCP_TIMEOUT", "30")),
    }


# Global client instance (managed by lifespan)
_mcp_client: Client | None = None


async def init_mcp_client():
    """Initialize global MCP client. Called during app startup."""
    global _mcp_client
    settings = get_mcp_settings()
    _mcp_client = Client(settings["url"], timeout=settings["timeout"])
    await _mcp_client.__aenter__()


async def close_mcp_client():
    """Close global MCP client. Called during app shutdown."""
    global _mcp_client
    if _mcp_client:
        await _mcp_client.__aexit__(None, None, None)
        _mcp_client = None


def get_mcp_client() -> Client:
    """Dependency to get MCP client instance."""
    if _mcp_client is None:
        raise HTTPException(503, detail="MCP client not initialized")
    return _mcp_client


# Type alias for dependency injection
MCPClient = Annotated[Client, Depends(get_mcp_client)]


async def call_mcp_tool(tool_name: str, args: dict) -> any:
    """
    Call an MCP tool and map errors to HTTP exceptions.

    This function maintains the same interface as before,
    but now uses FastMCP Client over HTTP transport.
    """
    client = get_mcp_client()

    try:
        result = await client.call_tool(tool_name, args)
        return result.data  # FastMCP returns CallToolResult, extract .data

    except ClientError as e:
        # Map error messages to HTTP status codes
        message = str(e)

        if "not found" in message.lower():
            raise HTTPException(404, detail=message)
        elif "cycle" in message.lower():
            raise HTTPException(409, detail=message)
        elif "validation" in message.lower() or "invalid" in message.lower():
            raise HTTPException(422, detail=message)
        else:
            raise HTTPException(422, detail=message)

    except ConnectionError as e:
        raise HTTPException(503, detail=f"MCP server unavailable: {e}")

    except TimeoutError as e:
        raise HTTPException(504, detail=f"MCP server timeout: {e}")

    except Exception as e:
        raise HTTPException(500, detail=f"MCP client error: {e}")
```

---

### 3. Route Updates

Routes need minimal changes - just make `call_mcp_tool` async:

**Before:**
```python
@router.get("")
async def list_companies(current_user: User = Depends(get_current_user)):
    return call_mcp_tool("pm_list_companies", {})  # Sync call
```

**After:**
```python
@router.get("")
async def list_companies(current_user: User = Depends(get_current_user)):
    return await call_mcp_tool("pm_list_companies", {})  # Async call
```

---

### 4. Application Lifespan

**Location:** `src/taskyn/web/backend/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from taskyn.web.backend.deps import init_mcp_client, close_mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_mcp_client()
    yield
    # Shutdown
    await close_mcp_client()


app = FastAPI(
    title="Taskyn Web API",
    lifespan=lifespan,
)
```

---

### 5. Health Check Endpoint

```python
@router.get("/health")
async def health_check(client: MCPClient):
    mcp_healthy = await client.health_check()

    return {
        "status": "healthy" if mcp_healthy else "degraded",
        "components": {
            "web": "healthy",
            "mcp": "healthy" if mcp_healthy else "unhealthy",
        }
    }
```

---

### 6. Docker Compose Configuration

**Location:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    environment:
      - TASKYN_DB=/data/taskyn.db
      - TASKYN_MCP_HOST=0.0.0.0
      - TASKYN_MCP_PORT=8000
    volumes:
      - taskyn-data:/data
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/mcp"]
      interval: 10s
      timeout: 5s
      retries: 3

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
    environment:
      - TASKYN_MCP_URL=http://mcp:8000/mcp
      - TASKYN_JWT_SECRET=${TASKYN_JWT_SECRET}
    ports:
      - "3000:3000"
    depends_on:
      mcp:
        condition: service_healthy

volumes:
  taskyn-data:
```

---

## Migration Strategy

### Phase 1: Update Dependencies
- Refactor `deps.py` to use FastMCP Client
- Add lifespan management to `main.py`
- Remove direct imports from `taskyn.mcp.server`
- Remove `_get_tool_func` helper

### Phase 2: Update Routes
- Add `await` to all `call_mcp_tool` calls
- Update route by route, test each

### Phase 3: Integration Testing
- Test full flow with MCP server running on HTTP
- Test error scenarios (MCP server down, timeout)

### Phase 4: Docker Configuration
- Create Dockerfiles
- Create docker-compose.yml
- Test two-container deployment

---

## Error Mapping Reference

| Taskyn Exception | MCP Error Message Pattern | HTTP Status |
|-----------------|---------------------------|-------------|
| NotFoundError | "not found" | 404 |
| CycleDetectedError | "cycle" | 409 |
| ValidationError | "validation", "invalid" | 422 |
| TaskynError | (other) | 422 |
| Connection Error | - | 503 |
| Timeout | - | 504 |
| Unknown | - | 500 |

---

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `TASKYN_MCP_URL` | (required) | MCP server endpoint (e.g., `http://mcp:8000/mcp`) |
| `TASKYN_MCP_TIMEOUT` | `30` | Request timeout in seconds |

**Note:** No default URL is provided - this forces explicit configuration and prevents accidental connections to wrong environments.
