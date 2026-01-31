"""Node CLI commands."""

from typing import Optional

import typer

from agentpm.cli.formatting import (
    console, create_nodes_table, create_time_entries_table,
    format_duration, short_id, get_status_style
)
from agentpm.cli.main import handle_errors, state

app = typer.Typer(help="Node management")


@app.command("list")
@handle_errors
def list_nodes(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project ID"),
    node_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by node type"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
    milestone: Optional[str] = typer.Option(None, "--milestone", "-m", help="Filter by milestone"),
):
    """List nodes with optional filters."""
    from agentpm.graph import list_nodes as _list_nodes

    nodes = _list_nodes(
        project_id=project,
        node_type=node_type,
        status=status,
        assignee=assignee,
        milestone_id=milestone,
    )

    if state.json_output:
        console.print_json(data=[n.model_dump(mode="json") for n in nodes])
    else:
        if not nodes:
            console.print("[dim]No nodes found[/dim]")
        else:
            table = create_nodes_table(nodes)
            console.print(table)


@app.command("create")
@handle_errors
def create_node(
    parent_or_project: str = typer.Argument(..., help="Project ID or parent node ID"),
    node_type: str = typer.Argument(..., help="Node type (story, task, etc.)"),
    title: str = typer.Argument(..., help="Node title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee"),
    milestone: Optional[str] = typer.Option(None, "--milestone", "-m", help="Milestone ID"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority (low, medium, high, critical)"),
    estimate: Optional[int] = typer.Option(None, "--estimate", "-e", help="Estimated minutes"),
    points: Optional[int] = typer.Option(None, "--points", help="Story points"),
):
    """Create a new node.

    The first argument can be either a project ID (for top-level nodes) or
    a parent node ID (to create a child node with automatic parent edge).
    """
    from agentpm.graph import create_node as _create_node, get_node, create_edge
    from agentpm.core import get_project

    # Try as project first, then as node
    project = get_project(parent_or_project)
    parent_node = None

    if project is not None:
        project_id = project.id
    else:
        # Try as parent node
        parent_node = get_node(parent_or_project)
        if parent_node is None:
            console.print(f"[red]Not found:[/red] '{parent_or_project}' is not a valid project or node ID")
            raise typer.Exit(1)
        project_id = parent_node.project_id

    node = _create_node(
        project_id=project_id,
        node_type=node_type,
        title=title,
        description=description,
        assignee=assignee,
        milestone_id=milestone,
        priority=priority,
        estimated_minutes=estimate,
        story_points=points,
        actor="cli",
    )

    # Create parent edge if created under a node
    if parent_node is not None:
        create_edge(
            source_id=node.id,
            target_id=parent_node.id,
            edge_type="parent",
            actor="cli",
        )

    if state.json_output:
        console.print_json(data=node.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created {node_type}: {node.title}")
        console.print(f"  ID: {node.id}")
        console.print(f"  Status: {node.status}")
        if parent_node:
            console.print(f"  Parent: {parent_node.title} [{short_id(parent_node.id)}]")


@app.command("show")
@handle_errors
def show_node(
    node_id: str = typer.Argument(..., help="Node ID"),
):
    """Show node details with edges and time."""
    from agentpm.graph import get_node, get_parents, get_children
    from agentpm.core import get_time_total, list_time_entries, get_node_tags

    node = get_node(node_id)
    if node is None:
        console.print(f"[red]Node not found:[/red] {node_id}")
        raise typer.Exit(1)
    node_id = node.id  # Use full ID

    parents = get_parents(node_id)
    children = get_children(node_id)
    time_total = get_time_total(node_id)
    time_entries = list_time_entries(node_id)
    tags = get_node_tags(node_id)

    if state.json_output:
        data = node.model_dump(mode="json")
        data["parents"] = [p.id for p in parents]
        data["children"] = [c.id for c in children]
        data["time_total_minutes"] = time_total
        data["tags"] = [t.name for t in tags]
        console.print_json(data=data)
    else:
        from rich.text import Text

        console.print(f"[bold]{node.title}[/bold]")
        console.print(f"  ID: {node.id}")
        console.print(f"  Type: {node.node_type}")
        console.print(Text.assemble(
            ("  Status: ", ""),
            (node.status, get_status_style(node.status)),
        ))
        console.print(f"  Priority: {node.priority}")
        console.print(f"  Assignee: {node.assignee or '-'}")
        console.print(f"  Milestone: {short_id(node.milestone_id) if node.milestone_id else '-'}")
        console.print(f"  Description: {node.description or '-'}")
        if node.blocked_reason:
            console.print(f"  [red]Blocked:[/red] {node.blocked_reason}")
        console.print()

        if tags:
            console.print(f"[bold]Tags:[/bold] {', '.join(t.name for t in tags)}")
            console.print()

        console.print(f"[bold]Hierarchy:[/bold]")
        console.print(f"  Parents: {len(parents)}")
        for p in parents:
            console.print(f"    - {p.title} ({p.node_type})")
        console.print(f"  Children: {len(children)}")
        for c in children:
            console.print(f"    - {c.title} ({c.node_type})")
        console.print()

        console.print(f"[bold]Time:[/bold]")
        console.print(f"  Estimated: {format_duration(node.estimated_minutes)}")
        console.print(f"  Logged: {format_duration(time_total)}")
        if time_entries:
            console.print(f"  Entries: {len(time_entries)}")


@app.command("update")
@handle_errors
def update_node(
    node_id: str = typer.Argument(..., help="Node ID"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="New assignee"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="New priority"),
):
    """Update a node."""
    from agentpm.graph import update_node as _update_node

    node = _update_node(
        node_id=node_id,
        title=title,
        description=description,
        status=status,
        assignee=assignee,
        priority=priority,
        actor="cli",
    )

    if state.json_output:
        console.print_json(data=node.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Updated node: {node.title}")


@app.command("start")
@handle_errors
def start_node(
    node_id: str = typer.Argument(..., help="Node ID"),
):
    """Start working on a node (sets in_progress + starts timer)."""
    from agentpm.core import start_node as _start_node

    node = _start_node(node_id, actor="cli")

    if state.json_output:
        console.print_json(data=node.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Started: {node.title}")
        console.print("  Timer running...")


@app.command("done")
@handle_errors
def complete_node(
    node_id: str = typer.Argument(..., help="Node ID"),
):
    """Complete a node (stops timer + sets done)."""
    from agentpm.core import complete_node as _complete_node, get_time_total

    node = _complete_node(node_id, actor="cli")
    time_spent = get_time_total(node_id)

    if state.json_output:
        data = node.model_dump(mode="json")
        data["time_total_minutes"] = time_spent
        console.print_json(data=data)
    else:
        console.print(f"[green]✓[/green] Completed: {node.title}")
        console.print(f"  Time logged: {format_duration(time_spent)}")


@app.command("block")
@handle_errors
def block_node(
    node_id: str = typer.Argument(..., help="Node ID"),
    reason: str = typer.Argument(..., help="Reason for blocking"),
):
    """Block a node with a reason."""
    from agentpm.core import block_node as _block_node

    node = _block_node(node_id, reason=reason, actor="cli")

    if state.json_output:
        console.print_json(data=node.model_dump(mode="json"))
    else:
        console.print(f"[yellow]⚠[/yellow] Blocked: {node.title}")
        console.print(f"  Reason: {reason}")


@app.command("unblock")
@handle_errors
def unblock_node(
    node_id: str = typer.Argument(..., help="Node ID"),
):
    """Unblock a node."""
    from agentpm.core import unblock_node as _unblock_node

    node = _unblock_node(node_id, actor="cli")

    if state.json_output:
        console.print_json(data=node.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Unblocked: {node.title}")


@app.command("delete")
@handle_errors
def delete_node(
    node_id: str = typer.Argument(..., help="Node ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a node."""
    from agentpm.graph import get_node, delete_node as _delete_node

    node = get_node(node_id)
    if node is None:
        console.print(f"[red]Node not found:[/red] {node_id}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete node '{node.title}'?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    result = _delete_node(node_id, actor="cli")

    if state.json_output:
        console.print_json(data={"deleted": result, "id": node_id})
    else:
        if result:
            console.print(f"[green]✓[/green] Deleted node: {node.title}")
        else:
            console.print(f"[red]Failed to delete node[/red]")
            raise typer.Exit(1)
