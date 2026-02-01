"""Export commands for Taskyn CLI."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from taskyn.cli.main import state

app = typer.Typer(name="export", help="Data export operations")
console = Console()


@app.command("json")
def export_json(
    output: str = typer.Option(
        "taskyn_export.json", "--output", "-o",
        help="Output file path"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p",
        help="Export only this project (by ID or name)"
    ),
    pretty: bool = typer.Option(
        True, "--pretty/--compact",
        help="Pretty print JSON (default: pretty)"
    ),
):
    """Export data as JSON."""
    from taskyn.core import (
        list_companies,
        get_company,
        list_projects,
        get_project,
        list_milestones,
        list_time_entries,
        list_tags,
        list_activity,
    )
    from taskyn.graph import list_nodes, list_edges

    data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "companies": [],
        "projects": [],
        "milestones": [],
        "nodes": [],
        "edges": [],
        "time_entries": [],
        "tags": [],
        "activity": [],
    }

    if project:
        # Try to find project by ID or name
        proj = get_project(project)
        if proj is None:
            # Try by name
            all_projects = list_projects()
            matches = [p for p in all_projects if p.name.lower() == project.lower()]
            if matches:
                proj = matches[0]

        if proj is None:
            console.print(f"[red]Error:[/red] Project not found: {project}")
            raise typer.Exit(1)

        # Export single project and related data
        company = get_company(proj.company_id)
        if company:
            data["companies"] = [company.model_dump()]

        data["projects"] = [proj.model_dump()]
        data["milestones"] = [m.model_dump() for m in list_milestones(proj.id)]
        data["nodes"] = [n.model_dump() for n in list_nodes(project_id=proj.id)]
        data["edges"] = [e.model_dump() for e in list_edges(project_id=proj.id)]

        # Get time entries for all nodes in project
        for node in data["nodes"]:
            entries = list_time_entries(node["id"])
            data["time_entries"].extend([e.model_dump() for e in entries])

        console.print(f"Exporting project: {proj.name}")
    else:
        # Export everything
        data["companies"] = [c.model_dump() for c in list_companies()]
        data["projects"] = [p.model_dump() for p in list_projects()]

        for proj in list_projects():
            data["milestones"].extend([m.model_dump() for m in list_milestones(proj.id)])

        data["nodes"] = [n.model_dump() for n in list_nodes()]
        data["edges"] = [e.model_dump() for e in list_edges()]

        # Get time entries for all nodes
        for node in data["nodes"]:
            entries = list_time_entries(node["id"])
            data["time_entries"].extend([e.model_dump() for e in entries])

        data["tags"] = [t.model_dump() for t in list_tags()]
        data["activity"] = [a.model_dump() for a in list_activity(limit=1000)]

    # Write output
    output_path = Path(output)
    indent = 2 if pretty else None

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str, ensure_ascii=False)

    size_kb = output_path.stat().st_size / 1024

    console.print(f"[green]✓[/green] Exported to: {output_path}")
    console.print(f"  Size: {size_kb:.1f} KB")
    console.print(f"  Companies: {len(data['companies'])}")
    console.print(f"  Projects: {len(data['projects'])}")
    console.print(f"  Nodes: {len(data['nodes'])}")
    console.print(f"  Time entries: {len(data['time_entries'])}")

    if state.json_output:
        # Return JSON to stdout for programmatic use
        print(json.dumps({"exported_to": str(output_path), "stats": {
            "companies": len(data["companies"]),
            "projects": len(data["projects"]),
            "nodes": len(data["nodes"]),
            "time_entries": len(data["time_entries"]),
        }}))
