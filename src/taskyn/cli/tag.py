"""Tag CLI commands."""

from typing import Optional

import typer

from taskyn.cli.formatting import console, create_tags_table, short_id
from taskyn.cli.main import handle_errors, state

app = typer.Typer(help="Tag management")


@app.command("list")
@handle_errors
def list_tags():
    """List all tags."""
    from taskyn.core import list_tags as _list_tags

    tags = _list_tags()

    if state.json_output:
        console.print_json(data=[t.model_dump(mode="json") for t in tags])
    else:
        if not tags:
            console.print("[dim]No tags found[/dim]")
        else:
            table = create_tags_table(tags)
            console.print(table)


@app.command("create")
@handle_errors
def create_tag(
    name: str = typer.Argument(..., help="Tag name"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="Tag color (e.g., #ff0000)"),
):
    """Create a new tag."""
    from taskyn.core import create_tag as _create_tag

    tag = _create_tag(name=name, color=color)

    if state.json_output:
        console.print_json(data=tag.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created tag: {tag.name}")
        console.print(f"  ID: {tag.id}")
        if color:
            console.print(f"  Color: {color}")


@app.command("add")
@handle_errors
def add_tag(
    node_id: str = typer.Argument(..., help="Node ID"),
    tag_name: str = typer.Argument(..., help="Tag name"),
):
    """Add a tag to a node."""
    from taskyn.core import tag_node
    from taskyn.graph import get_node

    node = get_node(node_id)
    if node is None:
        console.print(f"[red]Node not found:[/red] {node_id}")
        raise typer.Exit(1)

    tag_node(node_id, tag_name, actor="cli")

    if state.json_output:
        console.print_json(data={"node_id": node_id, "tag": tag_name, "action": "added"})
    else:
        console.print(f"[green]✓[/green] Added tag '{tag_name}' to: {node.title}")


@app.command("remove")
@handle_errors
def remove_tag(
    node_id: str = typer.Argument(..., help="Node ID"),
    tag_name: str = typer.Argument(..., help="Tag name"),
):
    """Remove a tag from a node."""
    from taskyn.core import untag_node
    from taskyn.graph import get_node

    node = get_node(node_id)
    if node is None:
        console.print(f"[red]Node not found:[/red] {node_id}")
        raise typer.Exit(1)

    result = untag_node(node_id, tag_name)

    if state.json_output:
        console.print_json(data={"node_id": node_id, "tag": tag_name, "action": "removed", "success": result})
    else:
        if result:
            console.print(f"[green]✓[/green] Removed tag '{tag_name}' from: {node.title}")
        else:
            console.print(f"[dim]Tag '{tag_name}' was not on node[/dim]")


@app.command("nodes")
@handle_errors
def list_nodes_by_tag(
    tag_name: str = typer.Argument(..., help="Tag name"),
):
    """List nodes with a specific tag."""
    from taskyn.core import list_nodes_by_tag as _list_nodes_by_tag
    from taskyn.cli.formatting import create_nodes_table

    nodes = _list_nodes_by_tag(tag_name)

    if state.json_output:
        console.print_json(data=[n.model_dump(mode="json") for n in nodes])
    else:
        if not nodes:
            console.print(f"[dim]No nodes with tag '{tag_name}'[/dim]")
        else:
            table = create_nodes_table(nodes)
            table.title = f"Nodes with tag: {tag_name}"
            console.print(table)
