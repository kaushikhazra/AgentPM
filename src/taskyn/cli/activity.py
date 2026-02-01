"""Activity CLI command."""

from typing import Optional

import typer

from taskyn.cli.formatting import console, create_activity_table
from taskyn.cli.main import handle_errors, state


@handle_errors
def activity(
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries"),
    entity: Optional[str] = typer.Option(None, "--entity", "-e", help="Filter by entity type"),
):
    """Show recent activity."""
    from taskyn.core import list_activity

    activities = list_activity(limit=limit, entity_type=entity)

    if state.json_output:
        console.print_json(data=[a.model_dump(mode="json") for a in activities])
    else:
        if not activities:
            console.print("[dim]No recent activity[/dim]")
        else:
            table = create_activity_table(activities)
            console.print(table)
