"""Milestone CLI commands."""

from datetime import date
from typing import Optional

import typer

from agentpm.cli.formatting import console, create_milestones_table, format_duration, short_id
from agentpm.cli.main import handle_errors, state

app = typer.Typer(help="Milestone management")


@app.command("list")
@handle_errors
def list_milestones(
    project_id: str = typer.Argument(..., help="Project ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """List milestones in a project."""
    from agentpm.core import list_milestones as _list_milestones

    milestones = _list_milestones(project_id=project_id, status=status)

    if state.json_output:
        console.print_json(data=[m.model_dump(mode="json") for m in milestones])
    else:
        if not milestones:
            console.print("[dim]No milestones found[/dim]")
        else:
            table = create_milestones_table(milestones)
            console.print(table)


@app.command("create")
@handle_errors
def create_milestone(
    project_id: str = typer.Argument(..., help="Project ID"),
    name: str = typer.Argument(..., help="Milestone name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description"),
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Target date (YYYY-MM-DD)"),
):
    """Create a new milestone."""
    from agentpm.core import create_milestone as _create_milestone

    target_date = None
    if target:
        try:
            target_date = date.fromisoformat(target)
        except ValueError:
            console.print(f"[red]Invalid date format:[/red] {target} (use YYYY-MM-DD)")
            raise typer.Exit(1)

    milestone = _create_milestone(
        project_id=project_id,
        name=name,
        description=description,
        target_date=target_date,
    )

    if state.json_output:
        console.print_json(data=milestone.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created milestone: {milestone.name}")
        console.print(f"  ID: {milestone.id}")
        if target_date:
            console.print(f"  Target: {target_date}")


@app.command("show")
@handle_errors
def show_milestone(
    milestone_id: str = typer.Argument(..., help="Milestone ID"),
):
    """Show milestone details with progress."""
    from agentpm.core import get_milestone, get_milestone_rollup
    from agentpm.graph import list_nodes

    milestone = get_milestone(milestone_id)
    if milestone is None:
        console.print(f"[red]Milestone not found:[/red] {milestone_id}")
        raise typer.Exit(1)

    rollup = get_milestone_rollup(milestone_id)
    nodes = list_nodes(milestone_id=milestone_id)

    if state.json_output:
        data = milestone.model_dump(mode="json")
        data["rollup"] = {
            "total_nodes": rollup.total_nodes,
            "completed_nodes": rollup.completed_nodes,
            "completion_percentage": rollup.completion_percentage,
            "total_time_minutes": rollup.total_time_minutes,
        }
        console.print_json(data=data)
    else:
        console.print(f"[bold]{milestone.name}[/bold]")
        console.print(f"  ID: {milestone.id}")
        console.print(f"  Status: {milestone.status}")
        console.print(f"  Target: {milestone.target_date or '-'}")
        console.print(f"  Description: {milestone.description or '-'}")
        console.print()
        console.print(f"[bold]Progress:[/bold]")
        console.print(f"  Nodes: {rollup.completed_nodes}/{rollup.total_nodes}")
        console.print(f"  Completion: {rollup.completion_percentage:.1f}%")
        console.print(f"  Time tracked: {format_duration(rollup.total_time_minutes)}")


@app.command("complete")
@handle_errors
def complete_milestone(
    milestone_id: str = typer.Argument(..., help="Milestone ID"),
):
    """Mark a milestone as complete."""
    from agentpm.core import complete_milestone as _complete_milestone

    milestone = _complete_milestone(milestone_id)

    if state.json_output:
        console.print_json(data=milestone.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Completed milestone: {milestone.name}")
