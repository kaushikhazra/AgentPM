"""Company detail screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class CompanyDetailScreen(Screen):
    """Full-screen view of company details."""

    DEFAULT_CSS = """
    CompanyDetailScreen {
        background: $surface;
    }

    #company-detail-content {
        padding: 2;
    }

    .detail-title {
        text-style: bold;
        padding-bottom: 1;
    }

    .detail-id {
        color: $text-muted;
    }

    .section-header {
        text-style: bold;
        color: $primary;
        padding-top: 1;
    }

    .project-item {
        padding: 0 2;
    }

    .project-item:hover {
        background: $surface-lighten-1;
    }

    .empty-message {
        color: $text-muted;
        padding: 0 2;
    }

    .meta-info {
        color: $text-muted;
        padding-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("n", "new_project", "New Project", show=True),
        Binding("d", "delete", "Delete", show=True),
    ]

    def __init__(self, company_id: str) -> None:
        super().__init__()
        self.company_id = company_id
        self.company = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="company-detail-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load company data when mounted."""
        self.load_company()

    def load_company(self) -> None:
        """Load company from database and render."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.company import get_company
            from taskyn.core.project import list_projects

            with get_db() as db:
                self.company = get_company(db, self.company_id)
                if not self.company:
                    self._render_not_found()
                    return

                # Get projects for this company
                projects = list_projects(db, company_id=self.company_id)
                self._render_company(projects)

        except Exception as e:
            self._render_error(str(e))

    def _render_company(self, projects: list) -> None:
        """Render the company details."""
        content = self.query_one("#company-detail-content", VerticalScroll)
        content.remove_children()

        company = self.company

        # Title section
        content.mount(
            Static(f"[bold]{company.name}[/bold]", classes="detail-title")
        )
        content.mount(Static(f"[dim]COMPANY - {company.id}[/dim]", classes="detail-id"))
        content.mount(Static("-" * 60))

        # Description
        if company.description:
            content.mount(Static(""))
            content.mount(Static(company.description))

        # Projects section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        content.mount(Static(f"[bold]Projects ({len(projects)})[/bold]", classes="section-header"))
        content.mount(Static(""))

        if projects:
            # Sort by status, then name
            status_order = {"active": 0, "on_hold": 1, "completed": 2, "archived": 3}
            projects.sort(key=lambda p: (status_order.get(p.status, 99), p.name))

            for project in projects:
                status_icon = {
                    "active": "[green]●[/]",
                    "on_hold": "[yellow]◐[/]",
                    "completed": "[cyan]✓[/]",
                    "archived": "[dim]○[/]",
                }.get(project.status, "○")

                content.mount(
                    Static(
                        f"  {status_icon} {project.name} [dim]({project.methodology})[/]",
                        classes="project-item",
                    )
                )
        else:
            content.mount(
                Static("[dim]No projects yet. Press 'n' to create one.[/dim]", classes="empty-message")
            )

        # Metadata section
        content.mount(Static(""))
        content.mount(Static("-" * 60))
        created = company.created_at.strftime("%Y-%m-%d %H:%M") if company.created_at else "Unknown"
        updated = company.updated_at.strftime("%Y-%m-%d %H:%M") if company.updated_at else "Unknown"
        content.mount(Static(f"Created: {created}", classes="meta-info"))
        content.mount(Static(f"Updated: {updated}", classes="meta-info"))

    def _render_not_found(self) -> None:
        """Render not found message."""
        content = self.query_one("#company-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static("[red]Company not found[/red]"))

    def _render_error(self, error: str) -> None:
        """Render error message."""
        content = self.query_one("#company-detail-content", VerticalScroll)
        content.remove_children()
        content.mount(Static(f"[red]Error: {error}[/red]"))

    def action_edit(self) -> None:
        """Open edit dialog."""
        if self.company:
            from taskyn.tui.dialogs.company_form import CompanyFormModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_company()
                    self.app._refresh_dashboard()

            self.app.push_screen(CompanyFormModal(self.company_id), on_dismiss)

    def action_new_project(self) -> None:
        """Create a new project under this company."""
        if self.company:
            from taskyn.tui.dialogs.project_form import ProjectFormModal

            def on_dismiss(result: bool) -> None:
                if result:
                    self.load_company()
                    self.app._refresh_dashboard()

            self.app.push_screen(ProjectFormModal(company_id=self.company_id), on_dismiss)

    def action_delete(self) -> None:
        """Delete this company."""
        if self.company:
            from taskyn.tui.dialogs.confirm import ConfirmDialog

            def on_dismiss(confirmed: bool) -> None:
                if confirmed:
                    self._delete_company()

            self.app.push_screen(
                ConfirmDialog(
                    message=f'Delete "{self.company.name}"?\n\nAll projects under this company will also be deleted.\nThis action cannot be undone.',
                    title="Delete Company",
                    confirm_label="Delete",
                    cancel_label="Cancel",
                    destructive=True,
                ),
                on_dismiss,
            )

    def _delete_company(self) -> None:
        """Delete the company."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.company import delete_company

            with get_db() as db:
                delete_company(db, self.company_id)

            self.app.notify(f"Deleted: {self.company.name}", title="Deleted")
            self.app._refresh_dashboard()
            self.app.pop_screen()

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")
