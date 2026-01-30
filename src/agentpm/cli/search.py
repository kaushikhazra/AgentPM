"""Search CLI command."""

from typing import Optional

import typer

from agentpm.cli.formatting import console, create_search_results_table
from agentpm.cli.main import handle_errors, state


@handle_errors
def search_cmd(
    query: str = typer.Argument(..., help="Search query"),
    entity_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by entity type (node, milestone, project)"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
):
    """Search across all entities."""
    from agentpm.core import search

    entity_types = [entity_type] if entity_type else None
    results = search(query=query, entity_types=entity_types, project_id=project, limit=limit)

    if state.json_output:
        data = [
            {
                "entity_type": r.entity_type,
                "entity_id": r.entity.id,
                "match_context": r.match_context,
                "relevance": r.relevance,
                "entity": r.entity.model_dump(mode="json"),
            }
            for r in results
        ]
        console.print_json(data=data)
    else:
        if not results:
            console.print(f"[dim]No results for '{query}'[/dim]")
        else:
            console.print(f"Found {len(results)} results for '[bold]{query}[/bold]'")
            console.print()
            table = create_search_results_table(results)
            console.print(table)
