"""Project detail screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


# Status display
STATUS_DISPLAY = {
    "active": ("● ACTIVE", "green"),
    "on_hold": ("◐ ON HOLD", "yellow"),
    "completed": ("✓ COMPLETED", "cyan"),
    "archived": ("○ ARCHIVED", "dim"),
}


class ProjectDetailScreen(Screen):
    """Full-screen view of project details."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("n", "new_milestone", "New Milestone", show=True),
        Binding("t", "new_task", "New Task", show=True),
        Binding("d", "delete", "Delete", show=True),
    ]

    def __init__(self, project_id: str) -> None:
        super().__init__()
        self.project_id = project_id
        self.project = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="project-detail-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load project data when mounted."""
        self.load_project()

    def load_project(self) -> None:
        """Load project from database and render."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import get_project
            from taskyn.core.milestone import list_milestones
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                self.project = get_project(db, self.project_id)
                if not self.project:
                    self._render_not_found()
                    return

                # Get milestones
                milestones = list_milestones(db, project_id=self.project_id)

                # Get tasks/stories for this project
                nodes = list_nodes(db, project_id=self.project_id)
                tasks = [n for n in nodes if n.node_type in ("task", "story")]

                self._render_project(milestones, tasks)

        except Exception as e:
            self._render_error(str(e))

    def _render_project(self, milestones: list, tasks: list) -> None:
        """Render the project details."""
        content = self.query_one("#project-detail-content", VerticalScroll)
        content.remove_children()

        project = self.project

        # Title section
        content.mount(
            Static(f"[bold]{project.name}[/bold]", classes="detail-title")
        )
        content.mount(Static(f"[dim]PROJECT - {project.id}[/dim]", classes="detail-id"))
        content.mount(Static("-" * 60))

        # Status and methodology
        status_text, status_color = STATUS_DISPLAY.get(project.status, ("?", ""))
        content.mount(Static(""))
        content.mount(
            Static(f"Status: [{status_color}]{status_text}[/]    Methodology: {project.methodology}")
        )

        # Description
        if project.description:
            content.mount(Static(""))
            content.mount(Static(project.description))

        # Quick stats
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        content.mount(Static("[bold]Quick Stats[/bold]", classes="section-header"))
        content.mount(Static(""))

        total_tasks = len(tasks)
        done_tasks = len([t for t in tasks if t.status == "done"])
        in_progress = len([t for t in tasks if t.status == "in_progress"])
        blocked = len([t for t in tasks if t.status == "blocked"])

        content.mount(Static(f"  Total Items: {total_tasks}", classes="stat-row"))
        content.mount(Static(f"  Completed: {done_tasks}", classes="stat-row"))
        content.mount(Static(f"  In Progress: {in_progress}", classes="stat-row"))
        if blocked:
            content.mount(Static(f"  [red]Blocked: {blocked}[/]", classes="stat-row"))

        # Milestones section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        content.mount(Static(f"[bold]Milestones ({len(milestones)})[/bold]", classes="section-header"))
        content.mount(Static(""))

        if milestones:
            # Sort by status, then target date
            for milestone in milestones:
                status_icon = "✓" if milestone.status == "completed" else "○"
                date_str = ""
                if milestone.target_date:
                    date_str = f" [dim]({milestone.target_date.strftime('%Y-%m-%d')})[/]"

                style = "strike dim" if milestone.status == "completed" else ""
                content.mount(
                    Static(
                        f"  {status_icon} [{style}]{milestone.name}[/]{date_str}",
                        classes="milestone-item",
                    )
                )
        else:
            content.mount(
                Static("[dim]No milestones yet. Press 'n' to create one.[/dim]", classes="empty-message")
            )

        # Recent tasks section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        content.mount(Static(f"[bold]Recent Tasks[/bold]", classes="section-header"))
        content.mount(Static(""))

        if tasks:
            # Show most recent 10 tasks
            recent_tasks = sorted(tasks, key=lambda t: t.updated_at or t.created_at, reverse=True)[:10]

            for task in recent_tasks:
                status_icons = {
                    "backlog": "○",
                    "ready": "●",
                    "in_progress": "◐",
                    "done": "✓",
                    "blocked": "✗",
                }
                icon = status_icons.get(task.status, "•")
                type_label = "[story]" if task.node_type == "story" else ""

                content.mount(
                    Static(
                        f"  {icon} {task.title} {type_label}",
                        classes="task-item",
                    )
                )

            if len(tasks) > 10:
                content.mount(Static(f"  [dim]... and {len(tasks) - 10} more[/dim]"))
        else:
            content.mount(
                Static("[dim]No tasks yet. Press 't' to create one.[/dim]", classes="empty-message")
            )

        # Metadata section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        created = project.created_at.strftime("%Y-%m-%d %H:%M") if project.created_at else "Unknown"
        updated = project.updated_at.strftime("%Y-%m-%d %H:%M") if project.updated_at else "Unknown"
        content.mount(Static(f"Created: {created}", classes="meta-info"))
        content.mount(Static(f"Updated: {updated}", classes="meta-info"))

    def _render_not_found(self) -> None:
        """Render not found message."""
        content = self.query_one("#project-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static("[red]Project not found[/red]"))

    def _render_error(self, error: str) -> None:
        """Render error message."""
        content = self.query_one("#project-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static(f"[red]Error: {error}[/red]"))

    def action_edit(self) -> None:
        """Open edit dialog."""
        if self.project:
            from taskyn.tui.dialogs.project_form import ProjectFormModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_project()
                    self.app._refresh_dashboard()

            self.app.push_screen(ProjectFormModal(self.project_id), on_dismiss)

    def action_new_milestone(self) -> None:
        """Create a new milestone under this project."""
        if self.project:
            from taskyn.tui.dialogs.milestone_form import MilestoneFormModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_project()
                    self.app._refresh_dashboard()

            self.app.push_screen(MilestoneFormModal(project_id=self.project_id), on_dismiss)

    def action_new_task(self) -> None:
        """Create a new task under this project."""
        if self.project:
            from taskyn.tui.dialogs.new_task import NewTaskModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_project()
                    self.app._refresh_dashboard()

            self.app.push_screen(NewTaskModal(project_id=self.project_id), on_dismiss)

    def action_delete(self) -> None:
        """Delete this project."""
        if self.project:
            from taskyn.tui.dialogs.confirm import ConfirmDialog

            def on_dismiss(confirmed: bool) -> None:
                if confirmed:
                    self._delete_project()

            self.app.push_screen(
                ConfirmDialog(
                    message=f'Delete "{self.project.name}"?\n\nAll milestones and tasks will also be deleted.\nThis action cannot be undone.',
                    title="Delete Project",
                    confirm_label="Delete",
                    cancel_label="Cancel",
                    destructive=True,
                ),
                on_dismiss,
            )

    def _delete_project(self) -> None:
        """Delete the project."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import delete_project

            with get_db() as db:
                delete_project(db, self.project_id)

            self.app.notify(f"Deleted: {self.project.name}", title="Deleted")
            self.app._refresh_dashboard()
            self.app.pop_screen()

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")
