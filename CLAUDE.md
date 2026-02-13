# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Taskyn is an AI-first personal project management system built in Python. It provides both a CLI and MCP server for managing projects, tasks, and time tracking.

## Architecture

```
src/taskyn/
├── db/                 # Database layer (SQLite)
│   ├── connection.py   # Connection management
│   ├── models.py       # Pydantic models
│   └── schema.py       # Schema initialization
├── graph/              # Graph layer (nodes & edges)
│   ├── nodes.py        # Node CRUD
│   ├── edges.py        # Edge CRUD
│   └── traversal.py    # Graph traversal
├── core/               # Business logic
│   ├── company.py      # Company management
│   ├── project.py      # Project management
│   ├── milestone.py    # Milestone management
│   ├── work_items.py   # Story/task helpers
│   ├── workflow.py     # Status transitions
│   ├── time_entry.py   # Time tracking
│   ├── tag.py          # Tagging system
│   ├── activity.py     # Activity logging
│   ├── rollup.py       # Aggregations
│   ├── reporting.py    # Dashboard, search
│   └── bulk.py         # Bulk operations
├── methodologies/      # PM methodologies
│   ├── base.py         # BaseMethodology ABC
│   ├── classic_agile.py
│   └── spec_driven.py
├── cli/                # Typer CLI
│   └── *.py            # Command modules
├── mcp/                # MCP server (FastMCP)
│   ├── server.py       # Tools & resources
│   └── __main__.py     # Entry point
└── exceptions.py       # Error types
```

## Build & Test Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_nodes.py

# Run with coverage
pytest --cov=taskyn

# Install in dev mode
pip install -e ".[dev]"
```

## Key Concepts

- **Methodology**: Defines valid node types, statuses, and transitions
- **Node**: Work item (story, task, spec, etc.)
- **Edge**: Relationship between nodes (parent, blocks, depends_on)
- **UNSET sentinel**: Used in update functions to distinguish "not provided" from "set to None"

## Task Time Tracking (Mandatory)

When implementing work that has Taskyn PM nodes:
1. **Start the timer** (`pm_start_timer`) on the node **before** you begin coding it
2. **Stop the timer** (`pm_stop_timer`) when the task is done or you switch to a different task
3. **Mark the node** status transitions as you go (`pm_start_node` → `pm_complete_node`)
4. Never leave a timer running on a completed task — stop it first, then mark done

This ensures accurate time tracking across all work.

## Coding Principles

- **Enum over string**: Always prefer enums over raw strings for fixed-value fields (e.g., methodology, entity type, status). Enums prevent typos, provide discoverability, and serve as a single source of truth. Define enums in `src/taskyn/db/enums.py`.

## Methodologies

- `classic_agile`: story → task, statuses: backlog/ready/in_progress/done
- `spec_driven`: spec → design → implementation → validation (gated workflow)

## CLI Entry Point

```bash
taskyn [command]  # Main CLI (defined in pyproject.toml as entry point)
```

## Standardized Ports

| Service | Port |
|---------|------|
| MCP Server | 8000 |
| Web UI | 3020 |
| HTTPS (Caddy) | 8030 |

All configuration files, Docker files, and documentation must use these ports. When adding or changing port references, grep the entire codebase to ensure consistency across: `docker-compose.yml`, `Dockerfile.web`, `vite.config.ts`, `main.py` CORS defaults, and all docs/specs.

## Browser Testing

Use **Puppeteer MCP** (not Chrome extension) for browser automation and testing. Deploy via Docker (`docker compose up --build -d`) and test against `http://localhost:3020`.

## MCP Server

```bash
python -m taskyn.mcp                              # stdio transport
python -m taskyn.mcp --transport streamable-http  # HTTP transport
```
