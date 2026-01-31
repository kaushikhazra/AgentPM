# AgentPM

AI-first personal project management system designed for both human and AI interaction.

## Features

- **Graph-based work tracking**: Nodes (stories, tasks) connected by edges (parent, depends_on)
- **Methodology system**: Classic Agile, Spec-Driven (Kiro-style), or create your own
- **Time tracking**: Timer-based or manual time logging
- **MCP Server**: Full Model Context Protocol support for AI assistants
- **CLI**: Rich command-line interface with JSON output support

## Installation

```bash
pip install agentpm
```

Or install from source:

```bash
git clone https://github.com/yourusername/agentpm.git
cd agentpm
pip install -e .
```

## Quick Start

### CLI Usage

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

### MCP Setup for Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

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

### MCP Setup for Claude Code

Add to your Claude Code MCP configuration:

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

### Running MCP with Streamable HTTP

For network access, run with streamable HTTP transport:

```bash
python -m agentpm.mcp --transport streamable-http --port 8000
```

## Docker Deployment

AgentPM can be deployed as a remote MCP server using Docker.

### Quick Start with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# Check container health
docker-compose ps

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The MCP server will be available at `http://localhost:8020/mcp`.

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

### Connecting to Remote MCP Server

Configure your MCP client to connect via HTTP:

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

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTPM_DB` | `/data/agentpm.db` | Database path inside container |
| `AGENTPM_ACTOR` | `mcp` | Actor ID for activity logs |
| `AGENTPM_MCP_HOST` | `0.0.0.0` | Bind to all interfaces |
| `AGENTPM_MCP_PORT` | `8020` | HTTP server port |

### Data Persistence

The SQLite database is stored at `/data/agentpm.db` inside the container. Mount a volume to `./data` on your host to persist data between container restarts:

```yaml
volumes:
  - ./data:/data
```

### Troubleshooting

**Container shows unhealthy:**
```bash
# Check container logs
docker-compose logs agentpm

# Verify MCP server is responding
curl http://localhost:8020/mcp
```

**Permission denied on database:**
The container runs as user `agentpm` (UID 1000). Ensure your host data directory is writable:
```bash
mkdir -p data
chmod 755 data
```

## Docker with HTTPS

For secure remote access, use the HTTPS configuration with Caddy reverse proxy.

### Quick Start (Local HTTPS)

```bash
# Start with self-signed certificate
docker-compose -f docker-compose.https.yml up -d

# Check status
docker-compose -f docker-compose.https.yml ps
```

Access: `https://localhost/mcp` (accept self-signed cert warning)

### Production Deployment

```bash
# Set your domain and optional email for Let's Encrypt
export DOMAIN=mcp.example.com
export EMAIL=admin@example.com

# Start with automatic Let's Encrypt certificate
docker-compose -f docker-compose.https.yml up -d
```

Access: `https://mcp.example.com/mcp`

### HTTPS Client Configuration

```json
{
  "mcpServers": {
    "agentpm": {
      "transport": "streamable-http",
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

### HTTPS Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | `localhost` | Domain for TLS certificate |
| `EMAIL` | - | Email for Let's Encrypt notifications (optional) |

### How It Works

- **Local**: Caddy generates a self-signed certificate for `localhost`
- **Production**: Caddy automatically obtains Let's Encrypt certificate
- **HTTP**: Requests to port 80 redirect to HTTPS (port 443)
- **Security**: HSTS, X-Content-Type-Options, X-Frame-Options headers

## CLI Commands

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

## MCP Tools

The MCP server exposes these tools:

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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTPM_DB` | Database file path | `~/.agentpm/agentpm.db` |
| `AGENTPM_ACTOR` | Actor ID for activity logs | `mcp` |
| `AGENTPM_MCP_PORT` | HTTP server port | `8000` |
| `AGENTPM_MCP_HOST` | HTTP server host | `127.0.0.1` |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=agentpm
```

## License

MIT
