"""Story CLI shortcuts."""

from typing import Optional

import typer

from agentpm.cli.formatting import console, create_nodes_table, short_id
from agentpm.cli.main import handle_errors, state

app = typer.Typer(help="Story shortcuts")


@app.command("list")
@handle_errors
def list_stories(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """List all stories."""
    from agentpm.graph import list_nodes

    nodes = list_nodes(project_id=project, node_type="story", status=status)

    if state.json_output:
        console.print_json(data=[n.model_dump(mode="json") for n in nodes])
    else:
        if not nodes:
            console.print("[dim]No stories found[/dim]")
        else:
            table = create_nodes_table(nodes)
            table.title = "Stories"
            console.print(table)


@app.command("create")
@handle_errors
def create_story(
    project_id: str = typer.Argument(..., help="Project ID"),
    title: str = typer.Argument(..., help="Story title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description"),
    milestone: Optional[str] = typer.Option(None, "--milestone", "-m", help="Milestone ID"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority"),
    points: Optional[int] = typer.Option(None, "--points", help="Story points"),
    criteria: Optional[str] = typer.Option(None, "--criteria", "-c", help="Acceptance criteria"),
):
    """Create a new story."""
    from agentpm.core import create_story as _create_story

    story = _create_story(
        project_id=project_id,
        title=title,
        description=description,
        milestone_id=milestone,
        priority=priority,
        story_points=points,
        acceptance_criteria=criteria,
        actor="cli",
    )

    if state.json_output:
        console.print_json(data=story.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created story: {story.title}")
        console.print(f"  ID: {story.id}")
        console.print(f"  Status: {story.status}")


@app.command("show")
@handle_errors
def show_story(
    story_id: str = typer.Argument(..., help="Story ID"),
):
    """Show story details with tasks."""
    from agentpm.core import get_story_with_tasks, get_node_rollup
    from agentpm.cli.formatting import format_duration, get_status_style
    from rich.text import Text

    result = get_story_with_tasks(story_id)
    story = result["story"]
    tasks = result["tasks"]
    rollup = get_node_rollup(story_id)

    if state.json_output:
        data = story.model_dump(mode="json")
        data["tasks"] = [t.model_dump(mode="json") for t in tasks]
        data["rollup"] = {
            "total_nodes": rollup.total_nodes,
            "completed_nodes": rollup.completed_nodes,
            "completion_percentage": rollup.completion_percentage,
            "total_time_minutes": rollup.total_time_minutes,
        }
        console.print_json(data=data)
    else:
        console.print(f"[bold]{story.title}[/bold]")
        console.print(f"  ID: {story.id}")
        console.print(Text.assemble(
            ("  Status: ", ""),
            (story.status, get_status_style(story.status)),
        ))
        console.print(f"  Priority: {story.priority}")
        console.print(f"  Story Points: {story.story_points or '-'}")
        console.print(f"  Description: {story.description or '-'}")

        if story.properties and story.properties.get("acceptance_criteria"):
            console.print(f"  Criteria: {story.properties['acceptance_criteria']}")

        console.print()
        console.print(f"[bold]Progress:[/bold]")
        completed_tasks = sum(1 for t in tasks if t.status == "done")
        console.print(f"  Tasks: {completed_tasks}/{len(tasks)}")
        console.print(f"  Completion: {rollup.completion_percentage:.1f}%")
        console.print(f"  Time: {format_duration(rollup.total_time_minutes)}")

        console.print()
        console.print(f"[bold]Tasks ({len(tasks)}):[/bold]")
        for task in tasks:
            status_text = Text(task.status, style=get_status_style(task.status))
            console.print(f"  [{short_id(task.id)}] {task.title} - ", status_text)
