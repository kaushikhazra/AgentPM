"""Rich formatting helpers for CLI output."""

from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def get_status_style(status: str) -> str:
    """Get Rich style for a status value."""
    styles = {
        "backlog": "dim",
        "ready": "blue",
        "todo": "white",
        "in_progress": "yellow",
        "blocked": "red",
        "in_review": "cyan",
        "done": "green",
        "cancelled": "dim strike",
        "active": "green",
        "on_hold": "yellow",
        "completed": "green",
        "archived": "dim",
        "open": "blue",
    }
    return styles.get(status, "white")


def format_duration(minutes: int | None) -> str:
    """Format duration in minutes to human readable string."""
    if minutes is None or minutes == 0:
        return "-"
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def format_date(dt: datetime | None) -> str:
    """Format datetime for display in local time."""
    if dt is None:
        return "-"
    # Treat naive datetimes as UTC, then convert to local
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone()
    return dt.strftime("%Y-%m-%d %H:%M")


def format_short_date(dt: datetime | None) -> str:
    """Format date only for display in local time."""
    if dt is None:
        return "-"
    # Treat naive datetimes as UTC, then convert to local
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone()
    return dt.strftime("%Y-%m-%d")


def truncate(text: str | None, max_length: int = 40) -> str:
    """Truncate text with ellipsis."""
    if text is None:
        return "-"
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def short_id(id_str: str | None) -> str:
    """Return first 8 characters of ID for display."""
    if id_str is None:
        return "-"
    return id_str[:8]


def create_companies_table(companies: list) -> Table:
    """Create a table for companies."""
    table = Table(title="Companies")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Created", style="dim")

    for company in companies:
        table.add_row(
            short_id(company.id),
            company.name,
            truncate(company.description),
            format_short_date(company.created_at),
        )

    return table


def create_projects_table(projects: list) -> Table:
    """Create a table for projects."""
    table = Table(title="Projects")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Methodology", style="dim")
    table.add_column("Created", style="dim")

    for project in projects:
        table.add_row(
            short_id(project.id),
            project.name,
            Text(project.status, style=get_status_style(project.status)),
            project.methodology,
            format_short_date(project.created_at),
        )

    return table


def create_milestones_table(milestones: list) -> Table:
    """Create a table for milestones."""
    table = Table(title="Milestones")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Target Date")
    table.add_column("Created", style="dim")

    for milestone in milestones:
        table.add_row(
            short_id(milestone.id),
            milestone.name,
            Text(milestone.status, style=get_status_style(milestone.status)),
            format_short_date(milestone.target_date) if milestone.target_date else "-",
            format_short_date(milestone.created_at),
        )

    return table


def create_nodes_table(nodes: list) -> Table:
    """Create a table for nodes."""
    table = Table(title="Nodes")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Type")
    table.add_column("Title", style="bold")
    table.add_column("Status")
    table.add_column("Assignee")
    table.add_column("Priority")

    for node in nodes:
        table.add_row(
            short_id(node.id),
            node.node_type,
            truncate(node.title, 30),
            Text(node.status, style=get_status_style(node.status)),
            node.assignee or "-",
            node.priority or "medium",
        )

    return table


def create_tags_table(tags: list) -> Table:
    """Create a table for tags."""
    table = Table(title="Tags")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="bold")
    table.add_column("Color")

    for tag in tags:
        color_text = tag.color or "-"
        if tag.color:
            color_text = Text(tag.color, style=f"on {tag.color}" if tag.color.startswith("#") else tag.color)
        table.add_row(
            short_id(tag.id),
            tag.name,
            str(color_text),
        )

    return table


def create_time_entries_table(entries: list) -> Table:
    """Create a table for time entries."""
    table = Table(title="Time Entries")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Started", style="dim")
    table.add_column("Duration")
    table.add_column("Notes")

    for entry in entries:
        table.add_row(
            short_id(entry.id),
            format_date(entry.started_at),
            format_duration(entry.duration_minutes),
            truncate(entry.notes) if entry.notes else "-",
        )

    return table


def create_activity_table(activities: list) -> Table:
    """Create a table for activity log entries."""
    table = Table(title="Activity")
    table.add_column("Time", style="dim")
    table.add_column("Entity")
    table.add_column("Action")
    table.add_column("Details")
    table.add_column("Actor")

    for activity in activities:
        details = ""
        if activity.old_value and activity.new_value:
            details = f"{activity.old_value} → {activity.new_value}"
        elif activity.new_value:
            details = activity.new_value
        elif activity.old_value:
            details = activity.old_value

        table.add_row(
            format_date(activity.created_at),
            f"{activity.entity_type}:{short_id(activity.entity_id)}",
            activity.action,
            truncate(details, 30),
            activity.actor or "-",
        )

    return table


def create_search_results_table(results: list) -> Table:
    """Create a table for search results."""
    table = Table(title="Search Results")
    table.add_column("Type")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title/Name", style="bold")
    table.add_column("Context")

    for result in results:
        entity = result.entity
        name = getattr(entity, "title", None) or getattr(entity, "name", "-")
        table.add_row(
            result.entity_type,
            short_id(entity.id),
            truncate(name, 30),
            truncate(result.match_context, 40),
        )

    return table


def create_dashboard_panel(dashboard: Any) -> Panel:
    """Create a panel for the dashboard view."""
    from rich.layout import Layout
    from rich.text import Text

    lines = []

    # Active timer
    if dashboard.active_timer and dashboard.active_timer_node:
        node = dashboard.active_timer_node
        elapsed = (datetime.now(dashboard.active_timer.started_at.tzinfo) - dashboard.active_timer.started_at).total_seconds() / 60
        lines.append(Text.assemble(
            ("  Active: ", "bold yellow"),
            (node.title, "bold"),
        ))
        lines.append(Text.assemble(
            ("  Timer: ", "dim"),
            (format_duration(int(elapsed)), "yellow"),
            (" running", "dim"),
        ))
        lines.append(Text(""))
    else:
        lines.append(Text.assemble(
            ("  No active timer", "dim"),
        ))
        lines.append(Text(""))

    # Today's time
    lines.append(Text.assemble(
        ("  Today: ", "dim"),
        (format_duration(dashboard.today_time_minutes), "cyan"),
        (" tracked", "dim"),
    ))
    lines.append(Text(""))

    # Blockers
    blocker_count = len(dashboard.blocked_nodes)
    if blocker_count > 0:
        lines.append(Text.assemble(
            ("  Blockers: ", "red"),
            (str(blocker_count), "bold red"),
        ))
        for node in dashboard.blocked_nodes[:3]:
            reason = node.blocked_reason or "No reason"
            lines.append(Text.assemble(
                ("    - ", "dim"),
                (truncate(reason, 40), "red"),
                (" on ", "dim"),
                (truncate(node.title, 20), ""),
            ))
    else:
        lines.append(Text.assemble(
            ("  Blockers: ", "dim"),
            ("0", "green"),
        ))
    lines.append(Text(""))

    # In progress
    in_progress_count = len(dashboard.in_progress_nodes)
    lines.append(Text.assemble(
        ("  In Progress: ", "dim"),
        (str(in_progress_count), "yellow" if in_progress_count > 0 else "dim"),
        (" items", "dim"),
    ))

    content = Text("\n").join(lines)
    return Panel(content, title="Taskyn Dashboard", border_style="blue")


def create_stats_panel(stats: Any, project_name: str) -> Panel:
    """Create a panel for project statistics."""
    lines = []

    # Node counts by type
    lines.append(Text.assemble(("  Nodes by Type:", "bold")))
    for node_type, count in stats.total_nodes.items():
        lines.append(Text.assemble(
            ("    ", ""),
            (node_type, "cyan"),
            (": ", "dim"),
            (str(count), "bold"),
        ))
    lines.append(Text(""))

    # Status breakdown
    lines.append(Text.assemble(("  Status Breakdown:", "bold")))
    for status, count in stats.nodes_by_status.items():
        lines.append(Text.assemble(
            ("    ", ""),
            (status, get_status_style(status)),
            (": ", "dim"),
            (str(count), "bold"),
        ))
    lines.append(Text(""))

    # Time tracked
    lines.append(Text.assemble(("  Time Tracked:", "bold")))
    lines.append(Text.assemble(
        ("    This week: ", "dim"),
        (format_duration(stats.time_this_week), "cyan"),
    ))
    lines.append(Text.assemble(
        ("    This month: ", "dim"),
        (format_duration(stats.time_this_month), "cyan"),
    ))
    lines.append(Text.assemble(
        ("    Total: ", "dim"),
        (format_duration(stats.time_total), "bold cyan"),
    ))
    lines.append(Text(""))

    # Velocity
    lines.append(Text.assemble(
        ("  Velocity: ", "dim"),
        (f"{stats.velocity_per_week:.1f}", "bold"),
        (" completions/week", "dim"),
    ))

    content = Text("\n").join(lines)
    return Panel(content, title=f"Stats: {project_name}", border_style="green")
