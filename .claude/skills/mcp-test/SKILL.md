---
name: mcp-test
description: Test MCP servers via stdio or streamable HTTP. Use when the user wants to test, debug, or explore MCP server tools and resources.
argument-hint: "<transport> <target> [options]"
allowed-tools: Bash, Read
---

# MCP Test Skill

Test MCP (Model Context Protocol) servers interactively. Supports both stdio and streamable-http transports.

## Usage

When invoked, analyze the user's request and run the appropriate MCP test command.

## Arguments

The skill accepts: `$ARGUMENTS`

Parse the arguments to determine:
1. **Transport**: `stdio` or `http`
2. **Target**: Command (for stdio) or URL (for http)
3. **Action**: What to do (list tools, call tool, etc.)

## Examples

```bash
# List tools from a local MCP server (stdio)
python scripts/mcp_test_client.py stdio "python -m agentpm.mcp" --list-tools

# List tools from a remote MCP server (HTTP)
python scripts/mcp_test_client.py http "http://localhost:8020" --list-tools

# Call a specific tool
python scripts/mcp_test_client.py stdio "python -m agentpm.mcp" --call pm_list_companies

# Call a tool with arguments
python scripts/mcp_test_client.py http "http://example.com:8020" --call pm_create_company '{"name": "Test"}'

# List resources
python scripts/mcp_test_client.py stdio "python -m agentpm.mcp" --list-resources

# Read a resource
python scripts/mcp_test_client.py http "http://localhost:8020" --read "pm://dashboard"

# Interactive mode
python scripts/mcp_test_client.py stdio "python -m agentpm.mcp" --interactive
```

## Common Patterns

### Quick Test (Default: AgentPM)
If no arguments provided, test the local AgentPM MCP server:
```bash
python scripts/mcp_test_client.py stdio "python -m agentpm.mcp" --list-tools --compact
```

### Remote Server Test
For HTTP URLs:
```bash
python scripts/mcp_test_client.py http "<url>" --list-tools
```

### With Authentication
```bash
python scripts/mcp_test_client.py http "<url>" -H "Authorization:Bearer <token>" --list-tools
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--list-tools` | `-l` | List available tools |
| `--list-resources` | `-r` | List available resources |
| `--call TOOL [ARGS]` | `-c` | Call a tool with optional JSON arguments |
| `--read URI` | | Read a resource by URI |
| `--interactive` | `-i` | Enter interactive mode |
| `--raw` | | Output raw JSON |
| `--compact` | | Compact output (names only) |
| `--quiet` | `-q` | Minimal output |
| `--env KEY=VALUE` | `-e` | Set environment variable (stdio only) |
| `--header KEY:VALUE` | `-H` | Set HTTP header (http only) |

## Workflow

1. Parse user's request to determine what they want to test
2. Construct and run the appropriate `mcp_test_client.py` command
3. Present results clearly
4. If user wants to explore further, suggest follow-up commands

## Notes

- For HTTP transport, the server must be running with `--transport streamable-http`
- HTTP transport requires `httpx` or `requests` package
- The script is located at `scripts/mcp_test_client.py`
