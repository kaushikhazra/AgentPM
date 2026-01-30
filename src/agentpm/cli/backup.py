"""Backup commands for AgentPM CLI."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentpm.config import get_database_path

app = typer.Typer(name="backup", help="Database backup operations")
console = Console()


def get_backup_dir() -> Path:
    """Get the default backup directory."""
    backup_dir = Path.home() / ".agentpm" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


@app.command("create")
def create_backup(
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Output path (default: ~/.agentpm/backups/agentpm_YYYYMMDD_HHMMSS.db)"
    ),
):
    """Create a backup of the database."""
    db_path = Path(get_database_path())

    if not db_path.exists():
        console.print("[red]Error:[/red] Database file not found")
        raise typer.Exit(1)

    if output:
        output_path = Path(output)
    else:
        backup_dir = get_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = backup_dir / f"agentpm_{timestamp}.db"

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(db_path, output_path)
    size_kb = output_path.stat().st_size / 1024

    console.print(f"[green]✓[/green] Backup created: {output_path}")
    console.print(f"  Size: {size_kb:.1f} KB")


@app.command("list")
def list_backups():
    """List existing backups."""
    backup_dir = get_backup_dir()

    if not backup_dir.exists():
        console.print("No backups found")
        return

    backups = sorted(backup_dir.glob("agentpm_*.db"), reverse=True)

    if not backups:
        console.print("No backups found")
        return

    table = Table(title="Database Backups")
    table.add_column("Filename", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Created", style="dim")

    for backup in backups:
        size_kb = backup.stat().st_size / 1024
        # Parse timestamp from filename
        try:
            ts_str = backup.stem.replace("agentpm_", "")
            created = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            created_str = created.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            created_str = "Unknown"

        table.add_row(backup.name, f"{size_kb:.1f} KB", created_str)

    console.print(table)


@app.command("restore")
def restore_backup(
    backup_file: str = typer.Argument(..., help="Backup file to restore"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite without confirmation"),
):
    """Restore database from a backup."""
    backup_path = Path(backup_file)

    # Check in backup directory if not absolute path
    if not backup_path.is_absolute() and not backup_path.exists():
        backup_path = get_backup_dir() / backup_file

    if not backup_path.exists():
        console.print(f"[red]Error:[/red] Backup file not found: {backup_file}")
        raise typer.Exit(1)

    db_path = Path(get_database_path())

    if db_path.exists() and not force:
        confirm = typer.confirm(
            f"This will overwrite the current database at {db_path}. Continue?"
        )
        if not confirm:
            console.print("Restore cancelled")
            raise typer.Exit(0)

    # Create backup of current database before restore
    if db_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = get_backup_dir() / f"agentpm_prerestore_{timestamp}.db"
        shutil.copy2(db_path, pre_restore_backup)
        console.print(f"[dim]Current database backed up to: {pre_restore_backup}[/dim]")

    shutil.copy2(backup_path, db_path)
    console.print(f"[green]✓[/green] Database restored from: {backup_path}")
