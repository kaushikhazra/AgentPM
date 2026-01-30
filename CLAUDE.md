# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

AgentPM is an AI-first personal project management system built in Python. It provides both a CLI and MCP server for managing projects, tasks, and time tracking.

## Architecture

```
src/agentpm/
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
pytest --cov=agentpm

# Install in dev mode
pip install -e ".[dev]"
```

## Key Concepts

- **Methodology**: Defines valid node types, statuses, and transitions
- **Node**: Work item (story, task, spec, etc.)
- **Edge**: Relationship between nodes (parent, blocks, depends_on)
- **UNSET sentinel**: Used in update functions to distinguish "not provided" from "set to None"

## Methodologies

- `classic_agile`: story → task, statuses: backlog/ready/in_progress/done
- `spec_driven`: spec → design → implementation → validation (gated workflow)

## CLI Entry Point

```bash
apm [command]  # Main CLI (defined in pyproject.toml as entry point)
```

## MCP Server

```bash
python -m agentpm.mcp                              # stdio transport
python -m agentpm.mcp --transport streamable-http  # HTTP transport
```
