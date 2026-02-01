"""Milestone detail screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class MilestoneDetailScreen(Screen):
    """Full-screen view of milestone details."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("n", "new_task", "New Task", show=True),
        Binding("c", "complete", "Complete", show=True),
        Binding("d", "delete", "Delete", show=True),
    ]

    def __init__(self, milestone_id: str) -> None:
        super().__init__()
        self.milestone_id = milestone_id
        self.milestone = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="milestone-detail-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load milestone data when mounted."""
        self.load_milestone()

    def load_milestone(self) -> None:
        """Load milestone from database and render."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.milestone import get_milestone
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                self.milestone = get_milestone(db, self.milestone_id)
                if not self.milestone:
                    self._render_not_found()
                    return

                # Get tasks for this milestone
                nodes = list_nodes(db, milestone_id=self.milestone_id)
                tasks = [n for n in nodes if n.node_type in ("task", "story")]

                self._render_milestone(tasks)

        except Exception as e:
            self._render_error(str(e))

    def _render_milestone(self, tasks: list) -> None:
        """Render the milestone details."""
        content = self.query_one("#milestone-detail-content", VerticalScroll)
        content.remove_children()

        milestone = self.milestone

        # Title section
        status_icon = "✓" if milestone.status == "completed" else "○"
        content.mount(
            Static(f"[bold]{status_icon} {milestone.name}[/bold]", classes="detail-title")
        )
        content.mount(Static(f"[dim]MILESTONE - {milestone.id}[/dim]", classes="detail-id"))
        content.mount(Static("-" * 60))

        # Status and target date
        content.mount(Static(""))
        status_color = "green" if milestone.status == "completed" else "yellow"
        status_text = milestone.status.upper()

        target_str = "Not set"
        if milestone.target_date:
            target_str = milestone.target_date.strftime("%Y-%m-%d")
            # Check if overdue
            from datetime import date
            if milestone.status != "completed" and milestone.target_date < date.today():
                target_str = f"[red]{target_str} (OVERDUE)[/]"

        content.mount(
            Static(f"Status: [{status_color}]{status_text}[/]    Target: {target_str}")
        )

        # Description
        if milestone.description:
            content.mount(Static(""))
            content.mount(Static(milestone.description))

        # Progress section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        content.mount(Static("[bold]Progress[/bold]", classes="section-header"))
        content.mount(Static(""))

        total_tasks = len(tasks)
        done_tasks = len([t for t in tasks if t.status == "done"])

        if total_tasks > 0:
            percent = int((done_tasks / total_tasks) * 100)
            bar_width = 40
            filled = int(bar_width * done_tasks / total_tasks)
            empty = bar_width - filled

            bar = "[green]" + "█" * filled + "[/][dim]" + "░" * empty + "[/]"
            content.mount(Static(f"  {bar} {percent}%", classes="progress-bar"))
            content.mount(Static(f"  {done_tasks} of {total_tasks} tasks completed", classes="stat-row"))
        else:
            content.mount(Static("  No tasks assigned to this milestone", classes="stat-row"))

        # Tasks section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        content.mount(Static(f"[bold]Tasks ({len(tasks)})[/bold]", classes="section-header"))
        content.mount(Static(""))

        if tasks:
            # Group by status
            status_order = {"in_progress": 0, "ready": 1, "backlog": 2, "blocked": 3, "done": 4}
            tasks.sort(key=lambda t: (status_order.get(t.status, 99), t.title))

            for task in tasks:
                status_icons = {
                    "backlog": "○",
                    "ready": "●",
                    "in_progress": "[yellow]◐[/]",
                    "done": "[green]✓[/]",
                    "blocked": "[red]✗[/]",
                }
                icon = status_icons.get(task.status, "•")
                type_label = " [dim](story)[/]" if task.node_type == "story" else ""

                style = "strike dim" if task.status == "done" else ""
                content.mount(
                    Static(
                        f"  {icon} [{style}]{task.title}[/]{type_label}",
                        classes="task-item",
                    )
                )
        else:
            content.mount(
                Static("[dim]No tasks yet. Press 'n' to create one.[/dim]", classes="empty-message")
            )

        # Metadata section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        created = milestone.created_at.strftime("%Y-%m-%d %H:%M") if milestone.created_at else "Unknown"
        updated = milestone.updated_at.strftime("%Y-%m-%d %H:%M") if milestone.updated_at else "Unknown"
        content.mount(Static(f"Created: {created}", classes="meta-info"))
        content.mount(Static(f"Updated: {updated}", classes="meta-info"))
        if milestone.completed_at:
            completed = milestone.completed_at.strftime("%Y-%m-%d %H:%M")
            content.mount(Static(f"Completed: {completed}", classes="meta-info"))

    def _render_not_found(self) -> None:
        """Render not found message."""
        content = self.query_one("#milestone-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static("[red]Milestone not found[/red]"))

    def _render_error(self, error: str) -> None:
        """Render error message."""
        content = self.query_one("#milestone-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static(f"[red]Error: {error}[/red]"))

    def action_edit(self) -> None:
        """Open edit dialog."""
        if self.milestone:
            from taskyn.tui.dialogs.milestone_form import MilestoneFormModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_milestone()
                    self.app._refresh_dashboard()

            self.app.push_screen(MilestoneFormModal(self.milestone_id), on_dismiss)

    def action_new_task(self) -> None:
        """Create a new task under this milestone."""
        if self.milestone:
            from taskyn.tui.dialogs.new_task import NewTaskModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_milestone()
                    self.app._refresh_dashboard()

            # Pass project_id from milestone
            self.app.push_screen(NewTaskModal(project_id=self.milestone.project_id), on_dismiss)

    def action_complete(self) -> None:
        """Mark milestone as completed."""
        if self.milestone and self.milestone.status != "completed":
            from taskyn.tui.dialogs.confirm import ConfirmDialog

            def on_dismiss(confirmed: bool) -> None:
                if confirmed:
                    self._complete_milestone()

            self.app.push_screen(
                ConfirmDialog(
                    message=f'Mark "{self.milestone.name}" as completed?',
                    title="Complete Milestone",
                    confirm_label="Complete",
                    cancel_label="Cancel",
                    destructive=False,
                ),
                on_dismiss,
            )

    def _complete_milestone(self) -> None:
        """Complete the milestone."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.milestone import complete_milestone

            with get_db() as db:
                complete_milestone(db, self.milestone_id)

            self.app.notify(f"Completed: {self.milestone.name}", title="Milestone Completed")
            self.load_milestone()
            self.app._refresh_dashboard()

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_delete(self) -> None:
        """Delete this milestone."""
        if self.milestone:
            from taskyn.tui.dialogs.confirm import ConfirmDialog

            def on_dismiss(confirmed: bool) -> None:
                if confirmed:
                    self._delete_milestone()

            self.app.push_screen(
                ConfirmDialog(
                    message=f'Delete "{self.milestone.name}"?\n\nThis action cannot be undone.',
                    title="Delete Milestone",
                    confirm_label="Delete",
                    cancel_label="Cancel",
                    destructive=True,
                ),
                on_dismiss,
            )

    def _delete_milestone(self) -> None:
        """Delete the milestone."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.milestone import delete_milestone

            with get_db() as db:
                delete_milestone(db, self.milestone_id)

            self.app.notify(f"Deleted: {self.milestone.name}", title="Deleted")
            self.app._refresh_dashboard()
            self.app.pop_screen()

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")
