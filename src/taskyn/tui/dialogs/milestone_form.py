"""Milestone form modal dialog."""

from datetime import datetime, date

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length, Regex
from textual.widgets import Button, Input, Label, Select, Static, TextArea


class MilestoneFormModal(ModalScreen[bool]):
    """Modal dialog for creating or editing a milestone."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        milestone_id: str | None = None,
        project_id: str | None = None,
    ) -> None:
        """Initialize the modal.

        Args:
            milestone_id: ID of milestone to edit (None for new milestone)
            project_id: Default project for new milestone
        """
        super().__init__()
        self.milestone_id = milestone_id
        self.default_project_id = project_id
        self._milestone = None
        self._projects: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        self._load_projects()

        name = ""
        description = ""
        target_date = ""
        project_id = self.default_project_id

        if self.milestone_id:
            self._load_milestone()
            if self._milestone:
                name = self._milestone.name
                description = self._milestone.description or ""
                if self._milestone.target_date:
                    target_date = self._milestone.target_date.strftime("%Y-%m-%d")
                project_id = self._milestone.project_id

        title = "Edit Milestone" if self.milestone_id else "Create New Milestone"

        with Vertical(classes="modal-dialog-wide"):
            yield Static(title, classes="dialog-title")

            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Input(
                        value=name,
                        placeholder="Milestone name",
                        id="name-input",
                        validators=[Length(minimum=1, maximum=100)],
                    )

            with Horizontal(classes="form-row"):
                yield Label("Project:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Select(
                        options=self._projects,
                        value=project_id if project_id else Select.BLANK,
                        allow_blank=True,
                        id="project-select",
                    )

            with Horizontal(classes="form-row"):
                yield Label("Target Date:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Input(
                        value=target_date,
                        placeholder="YYYY-MM-DD",
                        id="target-date-input",
                        validators=[Regex(r"^$|^\d{4}-\d{2}-\d{2}$")],
                    )

            with Horizontal(classes="form-row"):
                yield Label("Description:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield TextArea(text=description, id="description-input")

            yield Static("", id="form-error", classes="error-text")

            with Horizontal(classes="button-row"):
                button_text = "Update" if self.milestone_id else "Create"
                yield Button(button_text, variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_projects(self) -> None:
        """Load project options from database."""
        self._projects = [("(No Project)", "")]
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import list_projects

            with get_db() as db:
                projects = list_projects(db)
                for project in projects:
                    self._projects.append((project.name, project.id))
        except Exception:
            pass

    def _load_milestone(self) -> None:
        """Load milestone data from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.milestone import get_milestone

            with get_db() as db:
                self._milestone = get_milestone(db, self.milestone_id)
        except Exception:
            pass

    def on_mount(self) -> None:
        """Focus the name input when mounted."""
        self.query_one("#name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self._submit_form()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        if event.input.id == "name-input":
            self.query_one("#project-select", Select).focus()
        elif event.input.id == "target-date-input":
            self._submit_form()

    def _submit_form(self) -> None:
        """Validate and submit the form."""
        name = self.query_one("#name-input", Input).value.strip()
        project_id = self.query_one("#project-select", Select).value
        target_date_str = self.query_one("#target-date-input", Input).value.strip()
        description = self.query_one("#description-input", TextArea).text.strip()

        error_display = self.query_one("#form-error", Static)

        if not name:
            error_display.update("Name is required")
            self.query_one("#name-input", Input).focus()
            return

        if not project_id or project_id == Select.BLANK:
            error_display.update("Project is required")
            self.query_one("#project-select", Select).focus()
            return

        target_date: date | None = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                error_display.update("Target date must be YYYY-MM-DD format")
                self.query_one("#target-date-input", Input).focus()
                return

        error_display.update("")

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.milestone import create_milestone, update_milestone

            with get_db() as db:
                if self.milestone_id:
                    update_milestone(
                        db,
                        self.milestone_id,
                        name=name,
                        description=description if description else None,
                        target_date=target_date,
                    )
                    self.app.notify(f"Updated: {name}", title="Milestone Updated")
                else:
                    create_milestone(
                        db,
                        project_id=project_id,
                        name=name,
                        description=description if description else None,
                        target_date=target_date,
                    )
                    self.app.notify(f"Created: {name}", title="Milestone Created")

            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
