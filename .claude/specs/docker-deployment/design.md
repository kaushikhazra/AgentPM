# Docker Deployment Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Docker Container                       │ │
│  │                                                     │ │
│  │   ┌─────────────────────────────────────────────┐  │ │
│  │   │         AgentPM MCP Server                  │  │ │
│  │   │         (streamable-http)                   │  │ │
│  │   │         Port: 8020                          │  │ │
│  │   └─────────────────────────────────────────────┘  │ │
│  │                        │                            │ │
│  │                        ▼                            │ │
│  │   ┌─────────────────────────────────────────────┐  │ │
│  │   │           SQLite Database                   │  │ │
│  │   │           /data/agentpm.db                  │  │ │
│  │   └─────────────────────────────────────────────┘  │ │
│  │                        │                            │ │
│  └────────────────────────│────────────────────────────┘ │
│                           │ Volume Mount                  │
│                           ▼                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Host Directory                          │ │
│  │              ./data/agentpm.db                       │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Dockerfile Design

### Multi-Stage Build

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
- Install build dependencies
- Create virtual environment
- Install package

# Stage 2: Runtime
FROM python:3.11-slim
- Copy virtual environment from builder
- Set up non-root user
- Configure entrypoint
```

### Key Decisions

1. **Base Image**: `python:3.11-slim`
   - Small footprint (~120MB)
   - Includes pip and basic tools
   - Python 3.11 required by AgentPM

2. **Multi-Stage Build**
   - Stage 1: Build with dev tools
   - Stage 2: Runtime only, smaller image
   - Reduces final image size by ~50%

3. **Non-Root User**
   - Create `agentpm` user (UID 1000)
   - Run server as non-root for security
   - Volume must be writable by UID 1000

## Environment Variables

| Variable | Container Default | Description |
|----------|-------------------|-------------|
| `AGENTPM_DB` | `/data/agentpm.db` | SQLite database path |
| `AGENTPM_ACTOR` | `mcp` | Actor ID for activity logs |
| `AGENTPM_MCP_HOST` | `0.0.0.0` | Bind to all interfaces |
| `AGENTPM_MCP_PORT` | `8020` | HTTP server port |

## Volume Strategy

### Mount Point
- Container path: `/data`
- Contains: `agentpm.db` (SQLite database)

### Permissions
- Directory owned by `agentpm` user (UID 1000)
- Database file created with 644 permissions
- Parent directory needs 755 permissions

### docker-compose.yml Volume Config
```yaml
volumes:
  - ./data:/data
```

## Network Configuration

### Port Mapping
- Internal: 8020
- External: 8020 (configurable)

### Transport
- Protocol: HTTP (streamable-http MCP transport)
- Endpoint: `http://host:8020/mcp`

## Health Check

### Strategy
Use a simple HTTP request to verify the MCP server responds.

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8020/mcp')" || exit 1
```

### Considerations
- Start period: 5s (allow server to initialize)
- Interval: 30s (not too frequent)
- Timeout: 10s (reasonable for HTTP)
- Retries: 3 (before marking unhealthy)

## docker-compose.yml Structure

```yaml
version: '3.8'

services:
  agentpm:
    build: .
    image: agentpm:latest
    container_name: agentpm
    ports:
      - "8020:8020"
    volumes:
      - ./data:/data
    environment:
      - AGENTPM_DB=/data/agentpm.db
      - AGENTPM_ACTOR=mcp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8020/mcp')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

## .dockerignore

Exclude from build context:
- `.git/`
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `*.db`
- `.claude/`
- `tests/`
- `*.md` (except needed ones)
- `data/`

## Security Considerations

1. **Non-Root Execution**
   - Server runs as `agentpm` user
   - Limits damage from container escape

2. **Minimal Image**
   - Only production dependencies
   - No shell utilities beyond Python stdlib

3. **No Secrets in Image**
   - All configuration via environment variables
   - No hardcoded credentials

4. **Read-Only Filesystem** (optional)
   - Can run with `--read-only` flag
   - Only `/data` volume needs write access

## Deployment Commands

### Build
```bash
docker build -t agentpm .
```

### Run (standalone)
```bash
docker run -d \
  --name agentpm \
  -p 8020:8020 \
  -v $(pwd)/data:/data \
  -e AGENTPM_DB=/data/agentpm.db \
  agentpm
```

### Run (compose)
```bash
docker-compose up -d
```

### Stop
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### Test Connection
```bash
python scripts/mcp_test_client.py http "http://localhost:8020" --list-tools
```
