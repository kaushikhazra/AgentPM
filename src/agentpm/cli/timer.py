"""Timer CLI commands."""

from typing import Optional
from datetime import datetime, timezone

import typer

from agentpm.cli.formatting import console, format_duration, format_date, short_id
from agentpm.cli.main import handle_errors, state

app = typer.Typer(help="Time tracking")


@app.command("start")
@handle_errors
def start_timer(
    node_id: str = typer.Argument(..., help="Node ID to track time on"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Timer notes"),
):
    """Start a timer on a node."""
    from agentpm.core import start_timer as _start_timer
    from agentpm.graph import get_node

    node = get_node(node_id)
    if node is None:
        console.print(f"[red]Node not found:[/red] {node_id}")
        raise typer.Exit(1)

    entry = _start_timer(node_id, notes=notes, actor="cli")

    if state.json_output:
        console.print_json(data=entry.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Timer started on: {node.title}")
        console.print(f"  Entry ID: {short_id(entry.id)}")


@app.command("stop")
@handle_errors
def stop_timer():
    """Stop the active timer."""
    from agentpm.core import stop_timer as _stop_timer, get_active_timer

    active = get_active_timer()
    if active is None:
        console.print("[dim]No active timer[/dim]")
        raise typer.Exit(0)

    entry = _stop_timer(actor="cli")

    if state.json_output:
        console.print_json(data=entry.model_dump(mode="json") if entry else None)
    else:
        if entry:
            console.print(f"[green]✓[/green] Timer stopped")
            console.print(f"  Duration: {format_duration(entry.duration_minutes)}")
        else:
            console.print("[dim]No active timer[/dim]")


@app.command("status")
@handle_errors
def timer_status():
    """Show the active timer."""
    from agentpm.core import get_active_timer
    from agentpm.graph import get_node

    active = get_active_timer()

    if active is None:
        if state.json_output:
            console.print_json(data=None)
        else:
            console.print("[dim]No active timer[/dim]")
        return

    node = get_node(active.node_id)
    now = datetime.now(timezone.utc)
    started = active.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    elapsed = int((now - started).total_seconds() / 60)

    if state.json_output:
        data = active.model_dump(mode="json")
        data["elapsed_minutes"] = elapsed
        data["node_title"] = node.title if node else None
        console.print_json(data=data)
    else:
        console.print(f"[bold]Active Timer[/bold]")
        console.print(f"  Node: {node.title if node else 'Unknown'}")
        console.print(f"  Started: {format_date(active.started_at)}")
        console.print(f"  Elapsed: [yellow]{format_duration(elapsed)}[/yellow]")
        if active.notes:
            console.print(f"  Notes: {active.notes}")


@app.command("log")
@handle_errors
def log_time(
    node_id: str = typer.Argument(..., help="Node ID"),
    minutes: int = typer.Argument(..., help="Minutes to log"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes"),
):
    """Log time manually on a node."""
    from agentpm.core import log_time as _log_time
    from agentpm.graph import get_node

    node = get_node(node_id)
    if node is None:
        console.print(f"[red]Node not found:[/red] {node_id}")
        raise typer.Exit(1)

    entry = _log_time(node_id, duration_minutes=minutes, notes=notes, actor="cli")

    if state.json_output:
        console.print_json(data=entry.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Logged {format_duration(minutes)} on: {node.title}")
        console.print(f"  Entry ID: {short_id(entry.id)}")
