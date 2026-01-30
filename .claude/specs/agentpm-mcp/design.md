# AgentPM MCP Server - Design

## Technology Stack
- **MCP SDK**: Official `mcp` Python package
- **Transport**: stdio (primary), SSE (optional)
- **Async**: Full async/await support

## Module Structure

```
src/agentpm/
└── mcp/
    ├── __init__.py
    ├── server.py       # MCP server setup and entry point
    ├── tools.py        # Tool definitions
    └── resources.py    # Resource definitions
```

## Server Setup (mcp/server.py)

```python
import asyncio
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server

from agentpm.config import set_database_path
from .tools import register_tools
from .resources import register_resources

# Initialize server
server = Server("agentpm")

# Get actor from environment or default
def get_actor() -> str:
    return os.getenv("AGENTPM_ACTOR", "mcp")

async def main():
    # Configure database
    db_path = os.getenv("AGENTPM_DB")
    if db_path:
        set_database_path(db_path)

    # Register tools and resources
    register_tools(server)
    register_resources(server)

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Tool Definitions (mcp/tools.py)

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

def register_tools(server: Server):
    """Register all AgentPM tools with the MCP server"""

    # ============================================================
    # Company Tools
    # ============================================================

    @server.tool()
    async def pm_list_companies() -> list[dict]:
        """
        List all companies.

        Returns a list of companies with their basic info and project counts.
        """
        from agentpm.core import list_companies
        companies = list_companies()
        return [c.model_dump() for c in companies]

    @server.tool()
    async def pm_create_company(
        name: str,
        description: str | None = None
    ) -> dict:
        """
        Create a new company.

        Args:
            name: Company name
            description: Optional description

        Returns:
            The created company object
        """
        from agentpm.core import create_company
        company = create_company(name, description, actor=get_actor())
        return company.model_dump()

    @server.tool()
    async def pm_get_company(id: str) -> dict:
        """
        Get a company by ID with project summary.

        Args:
            id: Company ID

        Returns:
            Company object with list of projects
        """
        from agentpm.core import get_company, list_projects
        company = get_company(id)
        projects = list_projects(company_id=id)
        return {
            **company.model_dump(),
            "projects": [p.model_dump() for p in projects]
        }

    # ============================================================
    # Project Tools
    # ============================================================

    @server.tool()
    async def pm_list_projects(
        company_id: str | None = None,
        status: str | None = None
    ) -> list[dict]:
        """
        List projects with optional filters.

        Args:
            company_id: Filter by company
            status: Filter by status (active, on_hold, completed, archived)

        Returns:
            List of project objects
        """
        from agentpm.core import list_projects
        projects = list_projects(company_id=company_id, status=status)
        return [p.model_dump() for p in projects]

    @server.tool()
    async def pm_create_project(
        company_id: str,
        name: str,
        methodology: str = "classic_agile",
        description: str | None = None
    ) -> dict:
        """
        Create a new project.

        Args:
            company_id: Parent company ID
            name: Project name
            methodology: PM methodology (classic_agile, spec_driven, etc.)
            description: Optional description

        Returns:
            The created project object
        """
        from agentpm.core import create_project
        project = create_project(
            company_id, name, methodology, description,
            actor=get_actor()
        )
        return project.model_dump()

    @server.tool()
    async def pm_get_methodology_info(project_id: str) -> dict:
        """
        Get methodology information for a project.

        Returns valid node types, edge types, statuses, and transitions
        for the project's methodology.

        Args:
            project_id: Project ID

        Returns:
            Methodology definition with node_types, edge_types, etc.
        """
        from agentpm.core import get_project
        from agentpm.methodologies import get_methodology

        project = get_project(project_id)
        methodology = get_methodology(project.methodology)

        return {
            "name": methodology.name,
            "display_name": methodology.display_name,
            "node_types": {
                name: {
                    "valid_statuses": nt.valid_statuses,
                    "initial_status": nt.initial_status,
                    "terminal_statuses": list(nt.terminal_statuses),
                    "allowed_transitions": nt.allowed_transitions,
                }
                for name, nt in methodology.node_types.items()
            },
            "edge_types": {
                name: {
                    "source_types": et.source_types,
                    "target_types": et.target_types,
                    "max_per_source": et.max_per_source,
                    "allows_cycles": et.allows_cycles,
                }
                for name, et in methodology.edge_types.items()
            },
        }

    # ============================================================
    # Node Tools
    # ============================================================

    @server.tool()
    async def pm_list_nodes(
        project_id: str | None = None,
        node_type: str | None = None,
        status: str | None = None,
        assignee: str | None = None
    ) -> list[dict]:
        """
        List nodes (work items) with filters.

        Args:
            project_id: Filter by project
            node_type: Filter by type (story, task, etc.)
            status: Filter by status
            assignee: Filter by assignee

        Returns:
            List of node objects
        """
        from agentpm.graph import list_nodes
        nodes = list_nodes(
            project_id=project_id,
            node_type=node_type,
            status=status,
            assignee=assignee
        )
        return [n.model_dump() for n in nodes]

    @server.tool()
    async def pm_create_node(
        project_id: str,
        node_type: str,
        title: str,
        description: str | None = None,
        assignee: str | None = None,
        properties: dict | None = None
    ) -> dict:
        """
        Create a new node (work item).

        The node_type must be valid for the project's methodology.
        Use pm_get_methodology_info to see valid types.

        Args:
            project_id: Project ID
            node_type: Type of node (story, task, spec, etc.)
            title: Node title
            description: Optional description
            assignee: Optional assignee (human or AI identifier)
            properties: Optional methodology-specific properties

        Returns:
            The created node object
        """
        from agentpm.graph import create_node
        node = create_node(
            project_id=project_id,
            node_type=node_type,
            title=title,
            description=description,
            assignee=assignee,
            properties=properties,
            actor=get_actor()
        )
        return node.model_dump()

    @server.tool()
    async def pm_start_node(id: str) -> dict:
        """
        Start working on a node.

        Sets status to in_progress (or equivalent) and starts a timer.

        Args:
            id: Node ID

        Returns:
            The updated node object
        """
        from agentpm.core import start_node
        node = start_node(id, actor=get_actor())
        return node.model_dump()

    @server.tool()
    async def pm_complete_node(id: str) -> dict:
        """
        Complete a node.

        Stops any active timer and sets status to done (or equivalent terminal status).

        Args:
            id: Node ID

        Returns:
            The updated node object
        """
        from agentpm.core import complete_node
        node = complete_node(id, actor=get_actor())
        return node.model_dump()

    # ============================================================
    # Time Tracking Tools
    # ============================================================

    @server.tool()
    async def pm_start_timer(
        node_id: str,
        notes: str | None = None
    ) -> dict:
        """
        Start a timer on a node.

        If another timer is running, it will be automatically stopped.

        Args:
            node_id: Node to track time on
            notes: Optional notes about the work

        Returns:
            The created time entry object
        """
        from agentpm.core import start_timer
        entry = start_timer(node_id, notes=notes, actor=get_actor())
        return entry.model_dump()

    @server.tool()
    async def pm_stop_timer(
        node_id: str | None = None,
        entry_id: str | None = None
    ) -> dict | None:
        """
        Stop a running timer.

        If no arguments provided, stops the currently active timer.

        Args:
            node_id: Optional - stop timer on this node
            entry_id: Optional - stop specific time entry

        Returns:
            The stopped time entry, or None if no timer was running
        """
        from agentpm.core import stop_timer
        entry = stop_timer(entry_id=entry_id, actor=get_actor())
        return entry.model_dump() if entry else None

    @server.tool()
    async def pm_get_active_timer() -> dict | None:
        """
        Get the currently active timer.

        Returns:
            Active time entry with node info, or None
        """
        from agentpm.core import get_active_timer, get_node
        entry = get_active_timer()
        if not entry:
            return None

        node = get_node(entry.node_id)
        return {
            **entry.model_dump(),
            "node": node.model_dump() if node else None
        }

    # ============================================================
    # Reporting Tools
    # ============================================================

    @server.tool()
    async def pm_get_dashboard() -> dict:
        """
        Get the current dashboard summary.

        Returns:
            Dashboard with active timer, in-progress items, blockers, today's time
        """
        from agentpm.core import get_dashboard
        dashboard = get_dashboard()
        return {
            "active_timer": dashboard.active_timer.model_dump() if dashboard.active_timer else None,
            "active_timer_node": dashboard.active_timer_node.model_dump() if dashboard.active_timer_node else None,
            "in_progress_nodes": [n.model_dump() for n in dashboard.in_progress_nodes],
            "blocked_nodes": [n.model_dump() for n in dashboard.blocked_nodes],
            "today_time_minutes": dashboard.today_time_minutes,
            "recent_activity": [a.model_dump() for a in dashboard.recent_activity],
        }

    @server.tool()
    async def pm_search(query: str) -> list[dict]:
        """
        Search across all entities.

        Args:
            query: Search text

        Returns:
            List of matching entities with context
        """
        from agentpm.core import search
        results = search(query)
        return [
            {
                "entity_type": r.entity_type,
                "entity": r.entity.model_dump(),
                "match_context": r.match_context,
            }
            for r in results
        ]

    # ... more tools ...
```

## Resource Definitions (mcp/resources.py)

```python
from mcp.server import Server
from mcp.types import Resource, TextResourceContents

def register_resources(server: Server):
    """Register all AgentPM resources with the MCP server"""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources"""
        from agentpm.core import list_projects

        resources = [
            Resource(
                uri="pm://dashboard",
                name="Dashboard",
                description="Current work state summary",
                mimeType="application/json",
            ),
            Resource(
                uri="pm://activity/recent",
                name="Recent Activity",
                description="Recent activity feed",
                mimeType="application/json",
            ),
        ]

        # Add project resources
        for project in list_projects():
            resources.append(Resource(
                uri=f"pm://project/{project.id}",
                name=f"Project: {project.name}",
                description=project.description or f"Project {project.name}",
                mimeType="application/json",
            ))
            resources.append(Resource(
                uri=f"pm://project/{project.id}/methodology",
                name=f"Methodology: {project.name}",
                description=f"Valid types and transitions for {project.name}",
                mimeType="application/json",
            ))

        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> TextResourceContents:
        """Read a resource by URI"""
        import json

        if uri == "pm://dashboard":
            from agentpm.core import get_dashboard
            dashboard = get_dashboard()
            content = json.dumps({
                "active_timer": dashboard.active_timer.model_dump() if dashboard.active_timer else None,
                "in_progress_count": len(dashboard.in_progress_nodes),
                "blocked_count": len(dashboard.blocked_nodes),
                "today_time_minutes": dashboard.today_time_minutes,
            }, indent=2)
            return TextResourceContents(uri=uri, text=content, mimeType="application/json")

        if uri == "pm://activity/recent":
            from agentpm.core import list_activity
            activity = list_activity(limit=20)
            content = json.dumps([a.model_dump() for a in activity], indent=2)
            return TextResourceContents(uri=uri, text=content, mimeType="application/json")

        if uri.startswith("pm://project/"):
            parts = uri.replace("pm://project/", "").split("/")
            project_id = parts[0]

            if len(parts) == 1:
                # Project details
                from agentpm.core import get_project, get_project_stats
                project = get_project(project_id)
                stats = get_project_stats(project_id)
                content = json.dumps({
                    **project.model_dump(),
                    "stats": stats.__dict__,
                }, indent=2)
                return TextResourceContents(uri=uri, text=content, mimeType="application/json")

            if parts[1] == "methodology":
                # Methodology info
                from agentpm.core import get_project
                from agentpm.methodologies import get_methodology
                project = get_project(project_id)
                methodology = get_methodology(project.methodology)
                # ... format methodology info ...

        raise ValueError(f"Unknown resource: {uri}")
```

## Configuration for Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentpm": {
      "command": "python",
      "args": ["-m", "agentpm.mcp.server"],
      "env": {
        "AGENTPM_DB": "~/.agentpm/agentpm.db",
        "AGENTPM_ACTOR": "claude"
      }
    }
  }
}
```

For Claude Code, add to `~/.claude/claude_code_config.json` or use environment:

```json
{
  "mcpServers": {
    "agentpm": {
      "command": "python",
      "args": ["-m", "agentpm.mcp.server"],
      "env": {
        "AGENTPM_DB": "~/.agentpm/agentpm.db",
        "AGENTPM_ACTOR": "claude_code"
      }
    }
  }
}
```

## Error Handling

```python
from mcp.types import McpError, ErrorCode

def handle_agentpm_error(func):
    """Decorator to convert AgentPM errors to MCP errors"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundError as e:
            raise McpError(ErrorCode.InvalidParams, str(e))
        except ValidationError as e:
            raise McpError(ErrorCode.InvalidParams, str(e))
        except AgentPMError as e:
            raise McpError(ErrorCode.InternalError, str(e))
    return wrapper
```
