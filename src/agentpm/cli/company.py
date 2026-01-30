"""Company CLI commands."""

from typing import Optional

import typer

from agentpm.cli.formatting import console, create_companies_table, short_id
from agentpm.cli.main import handle_errors, state

app = typer.Typer(help="Company management")


@app.command("list")
@handle_errors
def list_companies():
    """List all companies."""
    from agentpm.core import list_companies as _list_companies

    companies = _list_companies()

    if state.json_output:
        console.print_json(data=[c.model_dump(mode="json") for c in companies])
    else:
        if not companies:
            console.print("[dim]No companies found[/dim]")
        else:
            table = create_companies_table(companies)
            console.print(table)


@app.command("create")
@handle_errors
def create_company(
    name: str = typer.Argument(..., help="Company name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Company description"),
):
    """Create a new company."""
    from agentpm.core import create_company as _create_company

    company = _create_company(name=name, description=description)

    if state.json_output:
        console.print_json(data=company.model_dump(mode="json"))
    else:
        console.print(f"[green]✓[/green] Created company: {company.name}")
        console.print(f"  ID: {company.id}")


@app.command("show")
@handle_errors
def show_company(
    company_id: str = typer.Argument(..., help="Company ID"),
):
    """Show company details."""
    from agentpm.core import get_company, list_projects

    company = get_company(company_id)
    if company is None:
        console.print(f"[red]Company not found:[/red] {company_id}")
        raise typer.Exit(1)

    projects = list_projects(company_id=company_id)

    if state.json_output:
        data = company.model_dump(mode="json")
        data["projects"] = [p.model_dump(mode="json") for p in projects]
        console.print_json(data=data)
    else:
        console.print(f"[bold]{company.name}[/bold]")
        console.print(f"  ID: {company.id}")
        console.print(f"  Description: {company.description or '-'}")
        console.print(f"  Created: {company.created_at}")
        console.print(f"  Projects: {len(projects)}")
        for project in projects:
            console.print(f"    - {project.name} ({project.status})")


@app.command("delete")
@handle_errors
def delete_company(
    company_id: str = typer.Argument(..., help="Company ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a company."""
    from agentpm.core import get_company, delete_company as _delete_company

    company = get_company(company_id)
    if company is None:
        console.print(f"[red]Company not found:[/red] {company_id}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete company '{company.name}'?")
        if not confirm:
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    result = _delete_company(company_id)

    if state.json_output:
        console.print_json(data={"deleted": result, "id": company_id})
    else:
        if result:
            console.print(f"[green]✓[/green] Deleted company: {company.name}")
        else:
            console.print(f"[red]Failed to delete company[/red]")
            raise typer.Exit(1)
