"""Stats CLI command."""

import typer

from taskyn.cli.formatting import console, create_stats_panel
from taskyn.cli.main import handle_errors, state


@handle_errors
def stats(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Show project statistics."""
    from taskyn.core import get_project, get_project_stats

    project = get_project(project_id)
    if project is None:
        console.print(f"[red]Project not found:[/red] {project_id}")
        raise typer.Exit(1)
    project_id = project.id  # Use full ID

    project_stats = get_project_stats(project_id)

    if state.json_output:
        data = {
            "project_id": project_id,
            "project_name": project.name,
            "total_nodes": project_stats.total_nodes,
            "nodes_by_status": project_stats.nodes_by_status,
            "time_this_week": project_stats.time_this_week,
            "time_this_month": project_stats.time_this_month,
            "time_total": project_stats.time_total,
            "velocity_per_week": project_stats.velocity_per_week,
            "blockers": [n.model_dump(mode="json") for n in project_stats.blockers],
            "milestone_progress": [
                {
                    "milestone": mp.milestone.model_dump(mode="json"),
                    "stats": {
                        "total_nodes": mp.stats.total_nodes,
                        "completed_nodes": mp.stats.completed_nodes,
                        "completion_percentage": mp.stats.completion_percentage,
                    }
                }
                for mp in project_stats.milestone_progress
            ],
        }
        console.print_json(data=data)
    else:
        panel = create_stats_panel(project_stats, project.name)
        console.print(panel)

        # Show milestone progress
        if project_stats.milestone_progress:
            console.print()
            console.print("[bold]Milestone Progress:[/bold]")
            for mp in project_stats.milestone_progress:
                pct = mp.stats.completion_percentage
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                console.print(f"  {mp.milestone.name}: [{bar}] {pct:.0f}%")
