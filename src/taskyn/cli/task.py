"""Task CLI shortcuts."""

from typing import Optional

import typer

from taskyn.cli.formatting import console, create_nodes_table, format_duration, short_id
from taskyn.cli.main import handle_errors, state

app = typer.Typer(help="Task shortcuts")


@app.command("list")
@handle_errors
def list_tasks(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Filter by assignee"),
):
    """List all tasks."""
    from taskyn.graph import list_nodes

    nodes = list_nodes(project_id=project, node_type="task", status=status, assignee=assignee)

    if state.json_output:
        console.print_json(data=[n.model_dump(mode="json") for n in nodes])
    else:
        if not nodes:
            console.print("[dim]No tasks found[/dim]")
        else:
            table = create_nodes_table(nodes)
            table.title = "Tasks"
            console.print(table)


@app.command("create")
@handle_errors
def create_task(
    story_id: str = typer.Argument(..., help="Parent story ID"),
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee"),
    estimate: Optional[int] = typer.Option(None, "--estimate", "-e", help="Estimated minutes"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority"),
):
    """Create a new task under a story."""
    from taskyn.core import create_task as _create_task

    task = _create_task(
        parent_id=story_id,
        title=title,
        description=description,
        assignee=assignee,
        estimated_minutes=estimate,
        priority=priority,
        actor="cli",
    )

    if state.json_output:
        console.print_json(data=task.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created task: {task.title}")
        console.print(f"  ID: {task.id}")
        console.print(f"  Parent: {short_id(story_id)}")
        console.print(f"  Status: {task.status}")


@app.command("start")
@handle_errors
def start_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Start working on a task (sets in_progress + starts timer)."""
    from taskyn.core import start_node

    task = start_node(task_id, actor="cli")

    if state.json_output:
        console.print_json(data=task.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Started task: {task.title}")
        console.print("  Timer running...")


@app.command("done")
@handle_errors
def complete_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Complete a task (stops timer + sets done)."""
    from taskyn.core import complete_node, get_time_total

    task = complete_node(task_id, actor="cli")
    time_spent = get_time_total(task_id)

    if state.json_output:
        data = task.model_dump(mode="json")
        data["time_total_minutes"] = time_spent
        console.print_json(data=data)
    else:
        console.print(f"[green]✓[/green] Completed task: {task.title}")
        console.print(f"  Time logged: {format_duration(time_spent)}")


@app.command("block")
@handle_errors
def block_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    reason: str = typer.Argument(..., help="Reason for blocking"),
):
    """Block a task with a reason."""
    from taskyn.core import block_node

    task = block_node(task_id, reason=reason, actor="cli")

    if state.json_output:
        console.print_json(data=task.model_dump(mode="json"))
    else:
        console.print(f"[yellow]⚠[/yellow] Blocked task: {task.title}")
        console.print(f"  Reason: {reason}")


@app.command("unblock")
@handle_errors
def unblock_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Unblock a task."""
    from taskyn.core import unblock_node

    task = unblock_node(task_id, actor="cli")

    if state.json_output:
        console.print_json(data=task.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Unblocked task: {task.title}")
