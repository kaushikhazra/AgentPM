"""MCP Server using FastMCP."""

import os
from fastmcp import FastMCP

from taskyn.config import set_database_path

# Initialize FastMCP server
mcp = FastMCP("taskyn", instructions="""
Taskyn is an AI-first project management system.

Key concepts:
- Companies contain Projects
- Projects contain Nodes (work items like stories, tasks)
- Nodes are connected by Edges (parent, blocks, relates_to)
- Each project has a Methodology that defines valid node types, statuses, and transitions

Use pm_get_methodology_info to understand what's valid for a project.
""")


def get_actor() -> str:
    """Get actor identifier from environment or default."""
    return os.getenv("TASKYN_ACTOR", "mcp")


# Configure database from environment at import time
db_path = os.getenv("TASKYN_DB")
if db_path:
    set_database_path(db_path)


# ============================================================
# Company Tools
# ============================================================

@mcp.tool()
def pm_list_companies(include_stats: bool = False) -> list[dict]:
    """
    List all companies.

    Args:
        include_stats: Include per-company aggregated stats

    Returns:
        List of companies, optionally with inline stats
    """
    from taskyn.core import list_companies, list_projects, get_project_stats
    companies = list_companies()
    result = []

    for c in companies:
        data = c.model_dump()
        if include_stats:
            projects = list_projects(company_id=c.id)
            total_nodes = 0
            completed_nodes = 0
            total_time_minutes = 0

            for project in projects:
                stats = get_project_stats(project.id)
                total_nodes += sum(stats.total_nodes.values())
                completed_nodes += stats.nodes_by_status.get("done", 0)
                total_time_minutes += stats.time_total

            completion_pct = (
                round(completed_nodes / total_nodes * 100, 1)
                if total_nodes > 0 else 0
            )

            data["stats"] = {
                "total_projects": len(projects),
                "total_nodes": total_nodes,
                "completed_nodes": completed_nodes,
                "completion_percentage": completion_pct,
                "total_time_minutes": total_time_minutes,
            }
        result.append(data)

    return result


@mcp.tool()
def pm_create_company(
    name: str,
    description: str | None = None,
    type: str = "discovery"
) -> dict:
    """
    Create a new company.

    Args:
        name: Company name
        description: Optional description
        type: Lifecycle stage (discovery, potential, matured, engaged, active, dormant)

    Returns:
        The created company object
    """
    from taskyn.core import create_company
    from taskyn.db.enums import EntityType
    entity_type = EntityType(type)
    company = create_company(name, description, type=entity_type, actor=get_actor())
    return company.model_dump()


@mcp.tool()
def pm_get_company(company_id: str) -> dict:
    """
    Get a company by ID with project summary.

    Args:
        company_id: Company ID

    Returns:
        Company object with list of projects
    """
    from taskyn.core import get_company, list_projects
    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Company not found: {company_id}")
    projects = list_projects(company_id=company_id)
    return {
        **company.model_dump(),
        "projects": [p.model_dump() for p in projects]
    }


@mcp.tool()
def pm_update_company(
    company_id: str,
    name: str | None = None,
    description: str | None = None,
    type: str | None = None,
) -> dict:
    """
    Update a company.

    Args:
        company_id: Company ID
        name: New name (optional)
        description: New description (optional)
        type: New lifecycle stage (discovery, potential, matured, engaged, active, dormant)

    Returns:
        The updated company object
    """
    from taskyn.core import update_company
    from taskyn.db.enums import EntityType
    entity_type = EntityType(type) if type else None
    company = update_company(company_id, name=name, description=description, type=entity_type, actor=get_actor())
    if company is None:
        raise ValueError(f"Company not found: {company_id}")
    return company.model_dump()


@mcp.tool()
def pm_delete_company(company_id: str) -> bool:
    """
    Delete a company and all its associated data.

    Args:
        company_id: Company ID

    Returns:
        True if deleted successfully
    """
    from taskyn.core import delete_company
    return delete_company(company_id, actor=get_actor())


@mcp.tool()
def pm_get_company_stats(company_id: str) -> dict:
    """
    Get aggregated statistics for a company across all its projects.

    Args:
        company_id: Company ID

    Returns:
        Aggregated stats (project count, node counts, time, completion %)
    """
    from taskyn.core import get_company, list_projects, get_project_stats

    company = get_company(company_id)
    if company is None:
        raise ValueError(f"Company not found: {company_id}")

    projects = list_projects(company_id=company_id)

    total_nodes = 0
    completed_nodes = 0
    total_time_minutes = 0

    for project in projects:
        stats = get_project_stats(project.id)
        total_nodes += sum(stats.total_nodes.values())
        completed_nodes += stats.nodes_by_status.get("done", 0)
        total_time_minutes += stats.time_total

    completion_pct = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0

    return {
        "company_id": company_id,
        "total_projects": len(projects),
        "total_nodes": total_nodes,
        "completed_nodes": completed_nodes,
        "completion_percentage": round(completion_pct, 1),
        "total_time_minutes": total_time_minutes,
    }


# ============================================================
# Project Tools
# ============================================================

@mcp.tool()
def pm_list_projects(
    company_id: str | None = None,
    status: str | None = None,
    include_stats: bool = False
) -> list[dict]:
    """
    List projects with optional filters.

    Args:
        company_id: Filter by company
        status: Filter by status (active, on_hold, completed, archived)
        include_stats: Include per-project stats (node counts, completion %, time)

    Returns:
        List of project objects, optionally with inline stats
    """
    from taskyn.core import list_projects, get_project_stats
    projects = list_projects(company_id=company_id, status=status)
    result = []

    for p in projects:
        data = p.model_dump()
        if include_stats:
            stats = get_project_stats(p.id)
            total_nodes = sum(stats.total_nodes.values())
            completed_nodes = stats.nodes_by_status.get("done", 0)
            data["stats"] = {
                "total_nodes": total_nodes,
                "completed_nodes": completed_nodes,
                "completion_percentage": (
                    round(completed_nodes / total_nodes * 100, 1)
                    if total_nodes > 0 else 0
                ),
                "total_time_minutes": stats.time_total,
                "nodes_by_type": stats.total_nodes,
            }
        result.append(data)

    return result


@mcp.tool()
def pm_create_project(
    company_id: str,
    name: str,
    methodology: str = "classic_agile",
    description: str | None = None,
    type: str = "discovery"
) -> dict:
    """
    Create a new project.

    Args:
        company_id: Parent company ID
        name: Project name
        methodology: PM methodology (classic_agile, spec_driven, etc.)
        description: Optional description
        type: Lifecycle stage (discovery, potential, matured, engaged, active, dormant)

    Returns:
        The created project object
    """
    from taskyn.core import create_project
    from taskyn.db.enums import EntityType
    entity_type = EntityType(type)
    project = create_project(
        company_id, name, methodology, description,
        type=entity_type,
        actor=get_actor()
    )
    return project.model_dump()


@mcp.tool()
def pm_get_project(project_id: str) -> dict:
    """
    Get a project by ID with stats.

    Args:
        project_id: Project ID

    Returns:
        Project object with statistics
    """
    from taskyn.core import get_project, get_project_stats
    project = get_project(project_id)
    if project is None:
        raise ValueError(f"Project not found: {project_id}")
    stats = get_project_stats(project_id)

    # Calculate totals from by-type and by-status dicts
    total_nodes = sum(stats.total_nodes.values())
    completed_nodes = stats.nodes_by_status.get("done", 0)
    in_progress_nodes = stats.nodes_by_status.get("in_progress", 0)
    blocked_nodes = stats.nodes_by_status.get("blocked", 0)

    return {
        **project.model_dump(),
        "stats": {
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "in_progress_nodes": in_progress_nodes,
            "blocked_nodes": blocked_nodes,
            "total_time_minutes": stats.time_total,
        }
    }


@mcp.tool()
def pm_update_project(
    project_id: str,
    status: str | None = None,
    name: str | None = None,
    description: str | None = None,
    type: str | None = None
) -> dict:
    """
    Update a project.

    Args:
        project_id: Project ID
        status: New status (active, on_hold, completed, archived)
        name: New name
        description: New description
        type: New lifecycle stage (discovery, potential, matured, engaged, active, dormant)

    Returns:
        The updated project object
    """
    from taskyn.core import update_project
    from taskyn.db.enums import EntityType
    entity_type = EntityType(type) if type else None
    project = update_project(
        project_id,
        status=status,
        name=name,
        description=description,
        type=entity_type,
        actor=get_actor()
    )
    return project.model_dump()


@mcp.tool()
def pm_delete_project(project_id: str) -> bool:
    """
    Delete a project and all its associated data.

    Args:
        project_id: Project ID

    Returns:
        True if deleted successfully
    """
    from taskyn.core import delete_project
    return delete_project(project_id, actor=get_actor())


@mcp.tool()
def pm_get_methodology_info(project_id: str) -> dict:
    """
    Get methodology information for a project.

    Returns valid node types, edge types, statuses, and transitions.
    Use this to understand what operations are valid.

    Args:
        project_id: Project ID

    Returns:
        Methodology definition with node_types, edge_types, etc.
    """
    from taskyn.core import get_project
    from taskyn.methodologies import get_methodology

    project = get_project(project_id)
    if project is None:
        raise ValueError(f"Project not found: {project_id}")
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
# Milestone Tools
# ============================================================

@mcp.tool()
def pm_list_milestones(
    project_id: str,
    status: str | None = None
) -> list[dict]:
    """
    List milestones for a project.

    Args:
        project_id: Project ID
        status: Filter by status (active, completed)

    Returns:
        List of milestone objects
    """
    from taskyn.core import list_milestones
    milestones = list_milestones(project_id, status=status)
    return [m.model_dump() for m in milestones]


@mcp.tool()
def pm_create_milestone(
    project_id: str,
    name: str,
    target_date: str | None = None,
    description: str | None = None
) -> dict:
    """
    Create a new milestone.

    Args:
        project_id: Project ID
        name: Milestone name
        target_date: Target date (YYYY-MM-DD format)
        description: Optional description

    Returns:
        The created milestone object
    """
    from taskyn.core import create_milestone
    milestone = create_milestone(
        project_id, name,
        target_date=target_date,
        description=description,
        actor=get_actor()
    )
    return milestone.model_dump()


@mcp.tool()
def pm_complete_milestone(milestone_id: str) -> dict:
    """
    Mark a milestone as completed.

    Args:
        milestone_id: Milestone ID

    Returns:
        The updated milestone object
    """
    from taskyn.core import complete_milestone
    milestone = complete_milestone(milestone_id, actor=get_actor())
    return milestone.model_dump()


@mcp.tool()
def pm_get_milestone(milestone_id: str) -> dict:
    """
    Get a milestone by ID.

    Args:
        milestone_id: Milestone ID

    Returns:
        The milestone object
    """
    from taskyn.core import get_milestone
    milestone = get_milestone(milestone_id)
    if milestone is None:
        raise ValueError(f"Milestone not found: {milestone_id}")
    return milestone.model_dump()


@mcp.tool()
def pm_update_milestone(
    milestone_id: str,
    name: str | None = None,
    description: str | None = None,
    target_date: str | None = None,
) -> dict:
    """
    Update a milestone.

    Args:
        milestone_id: Milestone ID
        name: New name (optional)
        description: New description (optional)
        target_date: New target date as ISO string (optional)

    Returns:
        The updated milestone object
    """
    from datetime import date as date_type
    from taskyn.core import update_milestone
    td = date_type.fromisoformat(target_date) if target_date else None
    milestone = update_milestone(
        milestone_id, name=name, description=description,
        target_date=td, actor=get_actor(),
    )
    return milestone.model_dump()


@mcp.tool()
def pm_delete_milestone(milestone_id: str) -> bool:
    """
    Delete a milestone.

    Args:
        milestone_id: Milestone ID

    Returns:
        True if deleted successfully
    """
    from taskyn.core import delete_milestone
    result = delete_milestone(milestone_id, actor=get_actor())
    if not result:
        raise ValueError(f"Milestone not found: {milestone_id}")
    return result


# ============================================================
# Node Tools
# ============================================================

@mcp.tool()
def pm_list_nodes(
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
    from taskyn.graph import list_nodes
    from taskyn.core import get_project

    # Resolve short project_id to full ID
    if project_id:
        project = get_project(project_id)
        if project:
            project_id = project.id

    nodes = list_nodes(
        project_id=project_id,
        node_type=node_type,
        status=status,
        assignee=assignee
    )
    return [n.model_dump() for n in nodes]


@mcp.tool()
def pm_create_node(
    project_id: str,
    node_type: str,
    title: str,
    description: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    milestone_id: str | None = None,
    parent_id: str | None = None
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
        assignee: Optional assignee
        priority: Optional priority (low, medium, high, critical)
        milestone_id: Optional milestone ID
        parent_id: Optional parent node ID (creates parent edge)

    Returns:
        The created node object
    """
    from taskyn.graph import create_node, create_edge
    node = create_node(
        project_id=project_id,
        node_type=node_type,
        title=title,
        description=description,
        assignee=assignee,
        priority=priority,
        milestone_id=milestone_id,
        actor=get_actor()
    )

    # Create parent edge if parent_id provided
    # Edge direction: child (source) → parent (target)
    if parent_id:
        create_edge(
            source_id=node.id,
            target_id=parent_id,
            edge_type="parent",
            actor=get_actor()
        )

    return node.model_dump()


@mcp.tool()
def pm_get_node(node_id: str) -> dict:
    """
    Get a node by ID with edges and time entries.

    Args:
        node_id: Node ID

    Returns:
        Node object with edges and time tracking info
    """
    from taskyn.graph import get_node, list_edges
    from taskyn.core import list_time_entries, get_node_rollup

    node = get_node(node_id)
    if node is None:
        raise ValueError(f"Node not found: {node_id}")

    outgoing = list_edges(source_id=node_id)
    incoming = list_edges(target_id=node_id)
    time_entries = list_time_entries(node_id)
    rollup = get_node_rollup(node_id)

    return {
        **node.model_dump(),
        "outgoing_edges": [e.model_dump() for e in outgoing],
        "incoming_edges": [e.model_dump() for e in incoming],
        "time_entries": [t.model_dump() for t in time_entries],
        "rollup": {
            "total_time_minutes": rollup.total_time_minutes,
            "estimated_time_minutes": rollup.estimated_time_minutes,
            "total_nodes": rollup.total_nodes,
            "completed_nodes": rollup.completed_nodes,
            "completion_percentage": rollup.completion_percentage,
        }
    }


@mcp.tool()
def pm_update_node(
    node_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    milestone_id: str | None = None
) -> dict:
    """
    Update a node.

    Args:
        node_id: Node ID
        title: New title
        description: New description
        status: New status
        assignee: New assignee
        priority: New priority
        milestone_id: New milestone ID

    Returns:
        The updated node object
    """
    from taskyn.graph import update_node

    kwargs = {"actor": get_actor()}
    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if status is not None:
        kwargs["status"] = status
    if assignee is not None:
        kwargs["assignee"] = assignee
    if priority is not None:
        kwargs["priority"] = priority
    if milestone_id is not None:
        kwargs["milestone_id"] = milestone_id

    node = update_node(node_id, **kwargs)
    return node.model_dump()


@mcp.tool()
def pm_start_node(node_id: str) -> dict:
    """
    Start working on a node (workflow action).

    This is a workflow action that:
    1. Changes the node's status to in_progress
    2. Automatically starts a timer

    Use this when beginning work on a task. For timer-only operations,
    use pm_start_timer instead.

    Args:
        node_id: Node ID

    Returns:
        The updated node object
    """
    from taskyn.core import start_node
    node = start_node(node_id, actor=get_actor())
    return node.model_dump()


@mcp.tool()
def pm_complete_node(node_id: str) -> dict:
    """
    Complete a node.

    Stops any active timer and sets status to done.

    Args:
        node_id: Node ID

    Returns:
        The updated node object
    """
    from taskyn.core import complete_node
    node = complete_node(node_id, actor=get_actor())
    return node.model_dump()


@mcp.tool()
def pm_block_node(node_id: str, reason: str) -> dict:
    """
    Block a node with a reason.

    Args:
        node_id: Node ID
        reason: Why the node is blocked

    Returns:
        The updated node object
    """
    from taskyn.core import block_node
    node = block_node(node_id, reason, actor=get_actor())
    return node.model_dump()


@mcp.tool()
def pm_delete_node(node_id: str) -> bool:
    """
    Delete a node.

    Args:
        node_id: Node ID

    Returns:
        True if deleted successfully
    """
    from taskyn.graph import delete_node
    result = delete_node(node_id, actor=get_actor())
    if not result:
        raise ValueError(f"Node not found: {node_id}")
    return result


# ============================================================
# Edge Tools
# ============================================================

@mcp.tool()
def pm_list_edges(
    project_id: str | None = None,
    source_id: str | None = None,
    target_id: str | None = None,
    edge_type: str | None = None
) -> list[dict]:
    """
    List edges with filters.

    Args:
        project_id: Filter by project
        source_id: Filter by source node
        target_id: Filter by target node
        edge_type: Filter by type (parent, blocks, relates_to)

    Returns:
        List of edge objects
    """
    from taskyn.graph import list_edges, get_node
    from taskyn.core import get_project

    # Resolve short IDs to full IDs
    if project_id:
        project = get_project(project_id)
        if project:
            project_id = project.id
    if source_id:
        node = get_node(source_id)
        if node:
            source_id = node.id
    if target_id:
        node = get_node(target_id)
        if node:
            target_id = node.id

    edges = list_edges(
        project_id=project_id,
        source_id=source_id,
        target_id=target_id,
        edge_type=edge_type
    )
    return [e.model_dump() for e in edges]


@mcp.tool()
def pm_create_edge(
    source_id: str,
    target_id: str,
    edge_type: str
) -> dict:
    """
    Create an edge between two nodes.

    Args:
        source_id: Source node ID
        target_id: Target node ID
        edge_type: Type of edge (parent, blocks, relates_to)

    Returns:
        The created edge object
    """
    from taskyn.graph import create_edge
    edge = create_edge(
        source_id=source_id,
        target_id=target_id,
        edge_type=edge_type,
        actor=get_actor()
    )
    return edge.model_dump()


@mcp.tool()
def pm_delete_edge(edge_id: str) -> bool:
    """
    Delete an edge.

    Args:
        edge_id: Edge ID

    Returns:
        True if deleted
    """
    from taskyn.graph import delete_edge
    return delete_edge(edge_id, actor=get_actor())


@mcp.tool()
def pm_get_ancestors(node_id: str, edge_type: str | None = None) -> list[dict]:
    """
    Get ancestor nodes (traverse up the graph).

    Args:
        node_id: Starting node ID
        edge_type: Optional edge type filter

    Returns:
        List of ancestor nodes
    """
    from taskyn.graph import get_ancestors
    nodes = get_ancestors(node_id, edge_type=edge_type)
    return [n.model_dump() for n in nodes]


@mcp.tool()
def pm_get_descendants(node_id: str, edge_type: str | None = None) -> list[dict]:
    """
    Get descendant nodes (traverse down the graph).

    Args:
        node_id: Starting node ID
        edge_type: Optional edge type filter

    Returns:
        List of descendant nodes
    """
    from taskyn.graph import get_descendants
    nodes = get_descendants(node_id, edge_type=edge_type)
    return [n.model_dump() for n in nodes]


# ============================================================
# Time Tracking Tools
# ============================================================

@mcp.tool()
def pm_start_timer(node_id: str, notes: str | None = None) -> dict:
    """
    Start a timer on a node (timer-only, no status change).

    This is a pure time-tracking operation that does NOT change the node's status.
    If another timer is running, it will be automatically stopped.

    Use pm_start_node instead if you want to both change status AND start timing.

    Args:
        node_id: Node to track time on
        notes: Optional notes about the work

    Returns:
        The created time entry object
    """
    from taskyn.core import start_timer
    entry = start_timer(node_id, notes=notes, actor=get_actor())
    return entry.model_dump()


@mcp.tool()
def pm_stop_timer(entry_id: str | None = None) -> dict | None:
    """
    Stop a running timer.

    If no entry_id provided, stops the currently active timer.

    Args:
        entry_id: Optional - stop specific time entry

    Returns:
        The stopped time entry, or None if no timer was running
    """
    from taskyn.core import stop_timer
    entry = stop_timer(entry_id=entry_id, actor=get_actor())
    return entry.model_dump() if entry else None


@mcp.tool()
def pm_log_time(
    node_id: str,
    duration_minutes: int,
    notes: str | None = None
) -> dict:
    """
    Log time manually on a node.

    Args:
        node_id: Node ID
        duration_minutes: Duration in minutes
        notes: Optional notes

    Returns:
        The created time entry
    """
    from taskyn.core import log_time
    entry = log_time(node_id, duration_minutes, notes=notes, actor=get_actor())
    return entry.model_dump()


@mcp.tool()
def pm_get_active_timer() -> dict | None:
    """
    Get the currently active timer.

    Returns:
        Active time entry with node info, or None
    """
    from taskyn.core import get_active_timer
    from taskyn.graph import get_node

    entry = get_active_timer()
    if not entry:
        return None

    node = get_node(entry.node_id)
    return {
        **entry.model_dump(),
        "node": node.model_dump() if node else None
    }


@mcp.tool()
def pm_get_time_entry(entry_id: str) -> dict:
    """
    Get a time entry by ID.

    Args:
        entry_id: Time entry ID

    Returns:
        The time entry object
    """
    from taskyn.core.time_entry import get_time_entry
    entry = get_time_entry(entry_id)
    if entry is None:
        raise ValueError(f"Time entry not found: {entry_id}")
    return entry.model_dump()


@mcp.tool()
def pm_delete_time_entry(entry_id: str) -> bool:
    """
    Delete a time entry.

    Args:
        entry_id: Time entry ID

    Returns:
        True if deleted successfully
    """
    from taskyn.core.time_entry import delete_time_entry
    result = delete_time_entry(entry_id, actor=get_actor())
    if not result:
        raise ValueError(f"Time entry not found: {entry_id}")
    return result


# ============================================================
# Reporting Tools
# ============================================================

@mcp.tool()
def pm_get_dashboard() -> dict:
    """
    Get the current dashboard summary.

    Returns:
        Dashboard with active timer, in-progress items, blockers, today's time
    """
    from taskyn.core import get_dashboard
    dashboard = get_dashboard()
    return {
        "active_timer": dashboard.active_timer.model_dump() if dashboard.active_timer else None,
        "active_timer_node": dashboard.active_timer_node.model_dump() if dashboard.active_timer_node else None,
        "in_progress_nodes": [n.model_dump() for n in dashboard.in_progress_nodes],
        "blocked_nodes": [n.model_dump() for n in dashboard.blocked_nodes],
        "today_time_minutes": dashboard.today_time_minutes,
        "recent_activity": [a.model_dump() for a in dashboard.recent_activity],
    }


@mcp.tool()
def pm_get_project_stats(project_id: str) -> dict:
    """
    Get project statistics.

    Args:
        project_id: Project ID

    Returns:
        Project statistics
    """
    from taskyn.core import get_project_stats
    stats = get_project_stats(project_id)

    # Calculate totals from by-type and by-status dicts
    total_nodes = sum(stats.total_nodes.values())
    completed_nodes = stats.nodes_by_status.get("done", 0)
    in_progress_nodes = stats.nodes_by_status.get("in_progress", 0)
    blocked_nodes = stats.nodes_by_status.get("blocked", 0)

    return {
        "total_nodes": total_nodes,
        "completed_nodes": completed_nodes,
        "in_progress_nodes": in_progress_nodes,
        "blocked_nodes": blocked_nodes,
        "total_time_minutes": stats.time_total,
        "time_this_week": stats.time_this_week,
        "time_this_month": stats.time_this_month,
        "velocity_per_week": stats.velocity_per_week,
        "nodes_by_type": stats.total_nodes,
        "nodes_by_status": stats.nodes_by_status,
        "blockers": [n.model_dump() for n in stats.blockers],
        "milestone_progress": [
            {
                "milestone_id": mp.milestone.id,
                "milestone_name": mp.milestone.name,
                "total_nodes": mp.stats.total_nodes,
                "completed_nodes": mp.stats.completed_nodes,
                "completion_percentage": mp.stats.completion_percentage,
            }
            for mp in stats.milestone_progress
        ],
    }


@mcp.tool()
def pm_search(
    query: str,
    entity_type: str | None = None,
    project_id: str | None = None,
    limit: int = 20
) -> list[dict]:
    """
    Search across all entities.

    Args:
        query: Search text
        entity_type: Filter by type (company, project, node)
        project_id: Filter by project
        limit: Max results (default 20)

    Returns:
        List of matching entities with context
    """
    from taskyn.core import search

    entity_types = [entity_type] if entity_type else None
    results = search(query, entity_types=entity_types, project_id=project_id, limit=limit)
    return [
        {
            "entity_type": r.entity_type,
            "entity": r.entity.model_dump(),
            "match_context": r.match_context,
        }
        for r in results
    ]


@mcp.tool()
def pm_get_recent_activity(
    limit: int = 20,
    entity_type: str | None = None,
    entity_id: str | None = None
) -> list[dict]:
    """
    Get recent activity.

    Args:
        limit: Max results (default 20)
        entity_type: Filter by entity type
        entity_id: Filter by specific entity

    Returns:
        List of activity entries
    """
    from taskyn.core import list_activity
    activities = list_activity(
        limit=limit,
        entity_type=entity_type,
        entity_id=entity_id
    )
    return [a.model_dump() for a in activities]


@mcp.tool()
def pm_get_rollup(node_id: str) -> dict:
    """
    Get aggregated stats for a node and its descendants.

    Args:
        node_id: Node ID

    Returns:
        Rollup statistics
    """
    from taskyn.core import get_node_rollup
    rollup = get_node_rollup(node_id)
    return {
        "total_time_minutes": rollup.total_time_minutes,
        "estimated_time_minutes": rollup.estimated_time_minutes,
        "total_nodes": rollup.total_nodes,
        "completed_nodes": rollup.completed_nodes,
        "blocked_nodes": rollup.blocked_nodes,
        "in_progress_nodes": rollup.in_progress_nodes,
        "completion_percentage": rollup.completion_percentage,
        "story_points": rollup.story_points,
    }


# ============================================================
# Tag Tools
# ============================================================

@mcp.tool()
def pm_list_tags() -> list[dict]:
    """
    List all tags.

    Returns:
        List of tag objects
    """
    from taskyn.core import list_tags
    tags = list_tags()
    return [t.model_dump() for t in tags]


@mcp.tool()
def pm_create_tag(name: str, color: str | None = None) -> dict:
    """
    Create a new tag.

    Args:
        name: Tag name
        color: Optional color (hex code)

    Returns:
        The created tag object
    """
    from taskyn.core import create_tag
    tag = create_tag(name, color=color)
    return tag.model_dump()


@mcp.tool()
def pm_tag_node(node_id: str, tag_name: str) -> bool:
    """
    Add a tag to a node.

    Creates the tag if it doesn't exist.

    Args:
        node_id: Node ID
        tag_name: Tag name

    Returns:
        True if tag was added
    """
    from taskyn.core import tag_node
    tag_node(node_id, tag_name, actor=get_actor())
    return True


@mcp.tool()
def pm_untag_node(node_id: str, tag_name: str) -> bool:
    """
    Remove a tag from a node.

    Args:
        node_id: Node ID
        tag_name: Tag name

    Returns:
        True if tag was removed
    """
    from taskyn.core import untag_node
    return untag_node(node_id, tag_name, actor=get_actor())


@mcp.tool()
def pm_delete_tag(tag_name: str) -> dict:
    """
    Delete a tag from the system.

    This removes the tag from all nodes that have it.

    Args:
        tag_name: Tag name to delete

    Returns:
        Dict with 'deleted' (bool) and 'usage_count' (int - nodes that had this tag)
    """
    from taskyn.core.tag import delete_tag_by_name
    result = delete_tag_by_name(tag_name)
    if not result["deleted"]:
        raise ValueError(f"Tag not found: {tag_name}")
    return result


@mcp.tool()
def pm_get_tag_usage(tag_name: str) -> dict:
    """
    Get usage information for a tag.

    Args:
        tag_name: Tag name

    Returns:
        Dict with 'tag_name' and 'usage_count' (number of nodes using this tag)
    """
    from taskyn.core.tag import get_tag_usage_count, get_tag_by_name
    tag = get_tag_by_name(tag_name)
    if tag is None:
        raise ValueError(f"Tag not found: {tag_name}")
    return {
        "tag_name": tag_name,
        "usage_count": get_tag_usage_count(tag_name),
    }


# ============================================================
# Resources
# ============================================================

@mcp.resource("pm://dashboard")
def get_dashboard_resource() -> str:
    """Current work state summary."""
    import json
    from taskyn.core import get_dashboard
    dashboard = get_dashboard()
    return json.dumps({
        "active_timer": dashboard.active_timer.model_dump() if dashboard.active_timer else None,
        "active_timer_node": dashboard.active_timer_node.model_dump() if dashboard.active_timer_node else None,
        "in_progress_nodes": [n.model_dump() for n in dashboard.in_progress_nodes],
        "blocked_nodes": [n.model_dump() for n in dashboard.blocked_nodes],
        "today_time_minutes": dashboard.today_time_minutes,
    }, indent=2, default=str)


@mcp.resource("pm://activity/recent")
def get_recent_activity_resource() -> str:
    """Recent activity feed."""
    import json
    from taskyn.core import list_activity
    activities = list_activity(limit=20)
    return json.dumps([a.model_dump() for a in activities], indent=2, default=str)


@mcp.resource("pm://project/{project_id}")
def get_project_resource(project_id: str) -> str:
    """Project details with stats."""
    import json
    from taskyn.core import get_project, get_project_stats
    project = get_project(project_id)
    if project is None:
        raise ValueError(f"Project not found: {project_id}")
    stats = get_project_stats(project_id)

    # Calculate totals from by-type and by-status dicts
    total_nodes = sum(stats.total_nodes.values())
    completed_nodes = stats.nodes_by_status.get("done", 0)
    in_progress_nodes = stats.nodes_by_status.get("in_progress", 0)
    blocked_nodes = stats.nodes_by_status.get("blocked", 0)

    return json.dumps({
        **project.model_dump(),
        "stats": {
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "in_progress_nodes": in_progress_nodes,
            "blocked_nodes": blocked_nodes,
            "total_time_minutes": stats.time_total,
        },
    }, indent=2, default=str)


@mcp.resource("pm://project/{project_id}/methodology")
def get_methodology_resource(project_id: str) -> str:
    """Valid types, statuses, and transitions for a project."""
    import json
    from taskyn.core import get_project
    from taskyn.methodologies import get_methodology

    project = get_project(project_id)
    if project is None:
        raise ValueError(f"Project not found: {project_id}")
    methodology = get_methodology(project.methodology)

    return json.dumps({
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
            }
            for name, et in methodology.edge_types.items()
        },
    }, indent=2, default=str)


@mcp.resource("pm://node/{node_id}")
def get_node_resource(node_id: str) -> str:
    """Node details with edges."""
    import json
    from taskyn.graph import get_node, list_edges
    from taskyn.core import list_time_entries, get_node_rollup

    node = get_node(node_id)
    if node is None:
        raise ValueError(f"Node not found: {node_id}")

    outgoing = list_edges(source_id=node_id)
    incoming = list_edges(target_id=node_id)
    time_entries = list_time_entries(node_id)
    rollup = get_node_rollup(node_id)

    return json.dumps({
        **node.model_dump(),
        "outgoing_edges": [e.model_dump() for e in outgoing],
        "incoming_edges": [e.model_dump() for e in incoming],
        "time_entries": [t.model_dump() for t in time_entries],
        "rollup": {
            "total_time_minutes": rollup.total_time_minutes,
            "completion_percentage": rollup.completion_percentage,
        },
    }, indent=2, default=str)
