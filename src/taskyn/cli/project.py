"""Project CLI commands."""

from typing import Optional

import typer

from taskyn.cli.formatting import console, create_projects_table, format_duration, format_date, short_id
from taskyn.cli.main import handle_errors, state

app = typer.Typer(help="Project management")


@app.command("list")
@handle_errors
def list_projects(
    company: Optional[str] = typer.Option(None, "--company", "-c", help="Filter by company ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """List all projects."""
    from taskyn.core import list_projects as _list_projects

    projects = _list_projects(company_id=company, status=status)

    if state.json_output:
        console.print_json(data=[p.model_dump(mode="json") for p in projects])
    else:
        if not projects:
            console.print("[dim]No projects found[/dim]")
        else:
            table = create_projects_table(projects)
            console.print(table)


@app.command("create")
@handle_errors
def create_project(
    company_id: str = typer.Argument(..., help="Company ID"),
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Project description"),
    methodology: str = typer.Option("classic_agile", "--methodology", "-m", help="Methodology to use"),
):
    """Create a new project."""
    from taskyn.core import create_project as _create_project

    project = _create_project(
        company_id=company_id,
        name=name,
        description=description,
        methodology=methodology,
    )

    if state.json_output:
        console.print_json(data=project.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created project: {project.name}")
        console.print(f"  ID: {project.id}")
        console.print(f"  Methodology: {project.methodology}")


@app.command("show")
@handle_errors
def show_project(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Show project details with stats."""
    from taskyn.core import get_project, get_project_stats, list_milestones
    from taskyn.graph import list_nodes

    project = get_project(project_id)
    if project is None:
        console.print(f"[red]Project not found:[/red] {project_id}")
        raise typer.Exit(1)
    project_id = project.id  # Use full ID

    stats = get_project_stats(project_id)
    milestones = list_milestones(project_id)
    nodes = list_nodes(project_id=project_id)

    if state.json_output:
        data = project.model_dump(mode="json")
        data["stats"] = {
            "total_nodes": stats.total_nodes,
            "nodes_by_status": stats.nodes_by_status,
            "time_total": stats.time_total,
            "velocity_per_week": stats.velocity_per_week,
        }
        console.print_json(data=data)
    else:
        console.print(f"[bold]{project.name}[/bold]")
        console.print(f"  ID: {project.id}")
        console.print(f"  Status: {project.status}")
        console.print(f"  Methodology: {project.methodology}")
        console.print(f"  Description: {project.description or '-'}")
        console.print(f"  Created: {format_date(project.created_at)}")
        console.print()
        console.print(f"[bold]Stats:[/bold]")
        console.print(f"  Nodes: {sum(stats.total_nodes.values())}")
        for node_type, count in stats.total_nodes.items():
            console.print(f"    {node_type}: {count}")
        console.print(f"  Time tracked: {format_duration(stats.time_total)}")
        console.print(f"  Velocity: {stats.velocity_per_week:.1f}/week")
        console.print(f"  Milestones: {len(milestones)}")


@app.command("update")
@handle_errors
def update_project(
    project_id: str = typer.Argument(..., help="Project ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status"),
):
    """Update a project."""
    from taskyn.core import update_project as _update_project

    project = _update_project(
        project_id=project_id,
        name=name,
        description=description,
        status=status,
    )

    if project is None:
        console.print(f"[red]Project not found:[/red] {project_id}")
        raise typer.Exit(1)

    if state.json_output:
        console.print_json(data=project.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Updated project: {project.name}")


@app.command("delete")
@handle_errors
def delete_project(
    project_id: str = typer.Argument(..., help="Project ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a project."""
    from taskyn.core import get_project, delete_project as _delete_project

    project = get_project(project_id)
    if project is None:
        console.print(f"[red]Project not found:[/red] {project_id}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete project '{project.name}'?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    result = _delete_project(project_id)

    if state.json_output:
        console.print_json(data={"deleted": result, "id": project_id})
    else:
        if result:
            console.print(f"[green]✓[/green] Deleted project: {project.name}")
        else:
            console.print(f"[red]Failed to delete project[/red]")
            raise typer.Exit(1)
