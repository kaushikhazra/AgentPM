# AgentPM

AI-first personal project management system designed for both human and AI interaction.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [MCP Server Setup](#mcp-server-setup)
- [Docker Deployment](#docker-deployment)
- [Methodologies](#methodologies)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Features

- **Graph-based work tracking**: Nodes (stories, tasks) connected by edges (parent, depends_on)
- **Methodology system**: Classic Agile, Spec-Driven (Kiro-style), or create your own
- **Time tracking**: Timer-based or manual time logging
- **MCP Server**: Full Model Context Protocol support for AI assistants
- **CLI**: Rich command-line interface with JSON output support

## Installation

### Requirements

- Python 3.11 or higher

### From PyPI

```bash
pip install agentpm
```

### From Source (Development)

```bash
git clone https://github.com/yourusername/agentpm.git
cd agentpm
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check CLI is available
apm --help

# Check version
apm --version
```

## Quick Start

```bash
# Create a company
apm company create "ACME Corp"

# Create a project (default: classic_agile methodology)
apm project create <company_id> "Website Redesign"

# Create a story
apm story create <project_id> "User Authentication"

# Create tasks under the story
apm task create <story_id> "Design login form"
apm task create <story_id> "Implement backend"

# Start working on a task (starts timer)
apm task start <task_id>

# Complete the task (stops timer)
apm task done <task_id>

# View dashboard
apm dashboard

# Search across all entities
apm search "login"
```

## CLI Reference

### Company Management

```bash
apm company list                    # List all companies
apm company create "Name"           # Create company
apm company show <id>               # Show company details
apm company delete <id>             # Delete company
```

### Project Management

```bash
apm project list                    # List all projects
apm project create <company_id> "Name" [-m methodology]
apm project show <id>               # Show project with stats
apm project update <id> [options]   # Update project
```

### Story/Task Shortcuts

```bash
apm story create <project_id> "Title"
apm story list [--project <id>]
apm story show <id>

apm task create <parent_id> "Title"
apm task start <id>                 # Start work (sets status + timer)
apm task done <id>                  # Complete (stops timer)
apm task block <id> --reason "..."  # Block with reason
```

### Time Tracking

```bash
apm timer start <node_id>           # Start timer
apm timer stop                      # Stop active timer
apm timer status                    # Show active timer
apm timer log <node_id> <minutes>   # Log time manually
```

### Tags

```bash
apm tag list                        # List all tags
apm tag create "bug" --color red    # Create tag
apm tag add <node_id> "bug"         # Tag a node
apm tag remove <node_id> "bug"      # Remove tag
```

### Backup & Export

```bash
apm backup create                   # Create database backup
apm backup list                     # List backups
apm backup restore <file>           # Restore from backup

apm export json                     # Export all data as JSON
apm export json --project <id>      # Export single project
```

### Other Commands

```bash
apm dashboard                       # Current work summary
apm stats <project_id>              # Project statistics
apm search "query"                  # Search all entities
apm activity                        # Recent activity log
```

## MCP Server Setup

AgentPM provides an MCP (Model Context Protocol) server that allows AI assistants to manage projects directly.

### Transport Options

| Transport | Use Case | Command |
|-----------|----------|---------|
| **stdio** | Local AI clients (Claude Desktop, Claude Code) | `python -m agentpm.mcp` |
| **streamable-http** | Remote access, Docker, multiple clients | `python -m agentpm.mcp --transport streamable-http` |

### Claude Desktop (Local - Recommended)

Add to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agentpm": {
      "command": "python",
      "args": ["-m", "agentpm.mcp"],
      "env": {
        "AGENTPM_DB": "~/.agentpm/agentpm.db",
        "AGENTPM_ACTOR": "claude"
      }
    }
  }
}
```

After saving, **fully quit Claude Desktop** (check system tray) and restart.

### Claude Code (Local)

Add to `~/.claude/settings.json` or use `claude mcp add`:

```json
{
  "mcpServers": {
    "agentpm": {
      "command": "python",
      "args": ["-m", "agentpm.mcp"],
      "env": {
        "AGENTPM_DB": "~/.agentpm/agentpm.db",
        "AGENTPM_ACTOR": "claude_code"
      }
    }
  }
}
```

### Remote HTTP Server

Run the MCP server with HTTP transport:

```bash
# Start server on port 8000
python -m agentpm.mcp --transport streamable-http --port 8000

# Or with custom host binding
python -m agentpm.mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

### Connecting to Remote MCP Server

For clients that natively support streamable-http:

```json
{
  "mcpServers": {
    "agentpm": {
      "transport": "streamable-http",
      "url": "http://localhost:8020/mcp"
    }
  }
}
```

### Using mcp-proxy

For clients that don't support streamable-http directly, use [mcp-proxy](https://github.com/punkpeye/mcp-proxy):

```bash
# Install mcp-proxy
pip install mcp-proxy
```

Configure Claude Desktop to use mcp-proxy:

```json
{
  "mcpServers": {
    "agentpm": {
      "command": "mcp-proxy",
      "args": ["http://localhost:8020/mcp"]
    }
  }
}
```

### MCP Tools Reference

| Category | Tools |
|----------|-------|
| Company | `pm_list_companies`, `pm_create_company`, `pm_get_company` |
| Project | `pm_list_projects`, `pm_create_project`, `pm_get_project`, `pm_update_project`, `pm_get_methodology_info` |
| Milestone | `pm_list_milestones`, `pm_create_milestone`, `pm_complete_milestone` |
| Node | `pm_list_nodes`, `pm_create_node`, `pm_get_node`, `pm_update_node`, `pm_start_node`, `pm_complete_node`, `pm_block_node` |
| Edge | `pm_list_edges`, `pm_create_edge`, `pm_delete_edge`, `pm_get_ancestors`, `pm_get_descendants` |
| Timer | `pm_start_timer`, `pm_stop_timer`, `pm_log_time`, `pm_get_active_timer` |
| Reporting | `pm_get_dashboard`, `pm_get_project_stats`, `pm_search`, `pm_get_recent_activity`, `pm_get_rollup` |
| Tag | `pm_list_tags`, `pm_create_tag`, `pm_tag_node`, `pm_untag_node` |

## Docker Deployment

Deploy AgentPM as a remote MCP server using Docker.

### Quick Start (HTTP)

```bash
# Clone and navigate to project
git clone https://github.com/yourusername/agentpm.git
cd agentpm

# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

The MCP server will be available at `http://localhost:8020/mcp`.

### Quick Start (HTTPS)

For secure remote access with automatic TLS:

```bash
# Local development (self-signed certificate)
docker-compose -f docker-compose.https.yml up -d

# Production (Let's Encrypt certificate)
DOMAIN=mcp.example.com docker-compose -f docker-compose.https.yml up -d
```

The HTTPS server will be available at `https://localhost:8030/mcp` (local) or `https://mcp.example.com:8030/mcp` (production).

### Manual Docker Run

```bash
# Build the image
docker build -t agentpm .

# Run with volume mount for persistent storage
docker run -d \
  --name agentpm \
  -p 8020:8020 \
  -v $(pwd)/data:/data \
  agentpm
```

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTPM_DB` | `/data/agentpm.db` | Database path inside container |
| `AGENTPM_ACTOR` | `mcp` | Actor ID for activity logs |
| `AGENTPM_MCP_HOST` | `0.0.0.0` | Bind address |
| `AGENTPM_MCP_PORT` | `8020` | HTTP server port |
| `DOMAIN` | `localhost` | Domain for HTTPS (Caddy) |

### Data Persistence

The SQLite database is stored at `/data/agentpm.db` inside the container. Mount a volume to persist data:

```yaml
volumes:
  - ./data:/data
```

## Methodologies

### Classic Agile (default)

Node types: `story`, `task`
Edge types: `parent` (task → story), `depends_on`

Status workflow:
- Story: backlog → ready → in_progress → done
- Task: todo → in_progress → done

### Spec-Driven (Kiro-style)

Node types: `spec`, `design`, `implementation`, `validation`
Edge types: `gates`, `validates`, `depends_on`

Gated workflow:
1. Spec (draft → approved → done)
2. Design (draft → in_review → approved)
3. Implementation (todo → in_progress → in_review → done)
4. Validation (pending → in_progress → passed/failed)

Use with:
```bash
apm project create <company_id> "Project" -m spec_driven
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTPM_DB` | Database file path | `~/.agentpm/agentpm.db` |
| `AGENTPM_ACTOR` | Actor ID for activity logs | `mcp` |
| `AGENTPM_MCP_PORT` | HTTP server port | `8000` |
| `AGENTPM_MCP_HOST` | HTTP server host | `127.0.0.1` |

## Troubleshooting

### MCP Connection Issues

**"Server disconnected" in Claude Desktop**

1. Ensure the MCP server is running:
   ```bash
   # For HTTP transport
   curl http://localhost:8020/mcp
   ```

2. For stdio transport, verify Python is in PATH:
   ```bash
   python -m agentpm.mcp --help
   ```

3. Fully quit Claude Desktop (check system tray) and restart.

**"Not Acceptable" error with mcp-proxy**

The server uses streamable-http which requires SSE support. Try updating mcp-proxy:
```bash
pip install --upgrade mcp-proxy
```

Or use stdio transport instead (recommended for local use).

### Database Issues

**"Permission denied" on database**

Ensure the database directory exists and is writable:
```bash
mkdir -p ~/.agentpm
chmod 755 ~/.agentpm
```

For Docker, the container runs as user `agentpm` (UID 1000):
```bash
mkdir -p data
chmod 755 data
```

### Docker Issues

**Container shows unhealthy**

Check container logs:
```bash
docker-compose logs agentpm
```

Verify the MCP server is responding:
```bash
curl http://localhost:8020/mcp
```

**Port already in use**

Change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8021:8020"  # Use port 8021 instead
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=agentpm

# Run specific test file
pytest tests/test_nodes.py -v
```

## License

MIT
