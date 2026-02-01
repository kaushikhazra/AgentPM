"""Task detail screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Label


# Status display
STATUS_DISPLAY = {
    "backlog": ("○ BACKLOG", "status-backlog"),
    "todo": ("● TODO", "status-todo"),
    "ready": ("● READY", "status-ready"),
    "in_progress": ("◐ IN PROGRESS", "status-in_progress"),
    "done": ("✓ DONE", "status-done"),
    "blocked": ("✗ BLOCKED", "status-blocked"),
}

# Priority display
PRIORITY_DISPLAY = {
    "high": ("▲ HIGH", "priority-high"),
    "medium": ("─ MEDIUM", "priority-medium"),
    "low": ("▼ LOW", "priority-low"),
}


class TaskDetailScreen(Screen):
    """Full-screen view of task details."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("s", "change_status", "Status", show=True),
        Binding("t", "toggle_timer", "Timer", show=True),
        Binding("d", "delete", "Delete", show=True),
    ]

    def __init__(self, task_id: str) -> None:
        super().__init__()
        self.task_id = task_id
        self.task = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="task-detail-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load task data when mounted."""
        self.load_task()

    def load_task(self) -> None:
        """Load task from database and render."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import get_node
            from taskyn.graph.edges import get_children
            from taskyn.core.time_entry import get_time_entries

            with get_db() as db:
                self.task = get_node(db, self.task_id)
                if not self.task:
                    self._render_not_found()
                    return

                # Get subtasks
                subtask_edges = get_children(db, self.task_id, "parent")
                subtasks = []
                for edge in subtask_edges:
                    subtask = get_node(db, edge.to_node_id)
                    if subtask:
                        subtasks.append(subtask)

                # Get time entries
                time_entries = get_time_entries(db, self.task_id)

                self._render_task(subtasks, time_entries)

        except Exception as e:
            self._render_error(str(e))

    def _render_task(self, subtasks: list, time_entries: list) -> None:
        """Render the task details."""
        content = self.query_one("#task-detail-content", VerticalScroll)
        content.remove_children()

        task = self.task
        metadata = task.metadata or {}

        # Title section
        content.mount(
            Static(f"[bold]{task.title}[/bold]", classes="task-title")
        )
        content.mount(Static(f"[dim]{task.node_type.upper()} • {task.id}[/dim]"))
        content.mount(Static("─" * 60))

        # Status and Priority row
        status_text, status_class = STATUS_DISPLAY.get(
            task.status, ("? UNKNOWN", "status-backlog")
        )
        priority = metadata.get("priority", "medium")
        priority_text, priority_class = PRIORITY_DISPLAY.get(
            priority, ("─ MEDIUM", "priority-medium")
        )

        content.mount(Static(""))
        content.mount(
            Static(f"Status: [{status_class}]{status_text}[/]    Priority: [{priority_class}]{priority_text}[/]")
        )

        # Metadata row
        due_date = metadata.get("due_date", "Not set")
        estimate = metadata.get("estimate", "Not set")
        content.mount(
            Static(f"Due: {due_date}    Estimate: {estimate}")
        )

        # Description
        content.mount(Static(""))
        content.mount(Static("─" * 60))
        content.mount(Static("[bold]Description[/bold]"))
        content.mount(Static(""))

        description = task.description or "[dim]No description[/dim]"
        content.mount(Static(description))

        # Tags
        tags = metadata.get("tags", [])
        if tags:
            content.mount(Static(""))
            content.mount(Static("─" * 60))
            content.mount(Static("[bold]Tags[/bold]"))
            tag_str = " ".join(f"[{tag}]" for tag in tags)
            content.mount(Static(f"[cyan]{tag_str}[/cyan]"))

        # Subtasks
        if subtasks:
            content.mount(Static(""))
            content.mount(Static("─" * 60))
            content.mount(Static(f"[bold]Subtasks ({len(subtasks)})[/bold]"))
            content.mount(Static(""))

            for subtask in subtasks:
                icon = "✓" if subtask.status == "done" else "○"
                style = "strike dim" if subtask.status == "done" else ""
                content.mount(
                    Static(f"  {icon} [{style}]{subtask.title}[/]")
                )

        # Time entries
        if time_entries:
            content.mount(Static(""))
            content.mount(Static("─" * 60))

            # Calculate total time
            total_seconds = sum(
                (e.duration.total_seconds() if e.duration else 0)
                for e in time_entries
            )
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            total_str = f"{hours}h {minutes}m"

            content.mount(Static(f"[bold]Time Entries ({total_str} total)[/bold]"))
            content.mount(Static(""))

            for entry in time_entries[-5:]:  # Show last 5
                if entry.start_time:
                    date_str = entry.start_time.strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = "?"

                if entry.duration:
                    dur_mins = int(entry.duration.total_seconds() // 60)
                    dur_str = f"{dur_mins}m"
                else:
                    dur_str = "running..."

                note = f" - {entry.notes}" if entry.notes else ""
                content.mount(
                    Static(f"  {date_str}  ({dur_str}){note}")
                )

            if len(time_entries) > 5:
                content.mount(
                    Static(f"  [dim]... and {len(time_entries) - 5} more[/dim]")
                )

    def _render_not_found(self) -> None:
        """Render not found message."""
        content = self.query_one("#task-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static("[red]Task not found[/red]"))

    def _render_error(self, error: str) -> None:
        """Render error message."""
        content = self.query_one("#task-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static(f"[red]Error: {error}[/red]"))

    def action_edit(self) -> None:
        """Open edit dialog."""
        self.app.notify("Edit coming soon!", title="TODO")

    def action_change_status(self) -> None:
        """Open status picker."""
        self.app.notify("Status picker coming soon!", title="TODO")

    def action_toggle_timer(self) -> None:
        """Toggle timer for this task."""
        self.app.notify("Timer toggle coming soon!", title="TODO")

    def action_delete(self) -> None:
        """Delete this task."""
        self.app.notify("Delete confirmation coming soon!", title="TODO")
