# README Update Plan

## Objective
Enhance README.md with comprehensive documentation for installation, Docker deployment, CLI usage, and MCP server configuration.

## Changes

### 1. Improve Structure
- Add table of contents for easy navigation
- Reorganize sections for better flow

### 2. Installation Section
- **From PyPI**: `pip install agentpm`
- **From Source (Development)**: Clone + `pip install -e ".[dev]"`
- **Requirements**: Python 3.11+

### 3. MCP Server Configuration
Expand with detailed setup for different clients:
- **Claude Desktop (stdio)**: Direct python command
- **Claude Code (stdio)**: Same approach with different actor
- **Remote HTTP**: streamable-http transport
- **Using mcp-proxy**: For clients that don't support streamable-http natively
- **Troubleshooting**: Common issues and solutions

### 4. Docker Section
- Quick start with docker-compose
- Manual docker run
- HTTPS with Caddy (port 8030)
- Environment variables table
- Troubleshooting

### 5. CLI Reference
- Already comprehensive, minor formatting improvements

### 6. Add Troubleshooting Section
- MCP connection issues
- Database permission issues
- Docker health check failures
