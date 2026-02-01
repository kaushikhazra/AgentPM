"""Project form modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Select, Static, TextArea


METHODOLOGY_OPTIONS = [
    ("Classic Agile", "classic_agile"),
    ("Spec Driven", "spec_driven"),
]

STATUS_OPTIONS = [
    ("Active", "active"),
    ("On Hold", "on_hold"),
    ("Completed", "completed"),
    ("Archived", "archived"),
]


class ProjectFormModal(ModalScreen[bool]):
    """Modal dialog for creating or editing a project."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, project_id: str | None = None, company_id: str | None = None) -> None:
        """Initialize the modal.

        Args:
            project_id: ID of project to edit (None for new project)
            company_id: ID of company to create project under
        """
        super().__init__()
        self.project_id = project_id
        self.company_id = company_id
        self._project = None
        self._companies = []

    def compose(self) -> ComposeResult:
        self._load_data()

        name = ""
        description = ""
        methodology = "classic_agile"
        status = "active"
        selected_company = self.company_id

        if self.project_id and self._project:
            name = self._project.name
            description = self._project.description or ""
            methodology = self._project.methodology
            status = self._project.status
            selected_company = self._project.company_id

        title = "Edit Project" if self.project_id else "Create New Project"
        company_options = [(c.name, c.id) for c in self._companies]

        with Vertical(classes="modal-dialog-wide"):
            yield Static(title, classes="dialog-title")

            with Horizontal(classes="form-row"):
                yield Label("Company:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Select(
                        options=company_options,
                        value=selected_company,
                        id="company-select",
                        allow_blank=False,
                    )

            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Input(
                        value=name,
                        placeholder="Project name",
                        id="name-input",
                        validators=[Length(minimum=1, maximum=100)],
                    )

            with Horizontal(classes="form-row"):
                yield Label("Methodology:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Select(
                        options=METHODOLOGY_OPTIONS,
                        value=methodology,
                        id="methodology-select",
                        allow_blank=False,
                    )

            if self.project_id:
                with Horizontal(classes="form-row"):
                    yield Label("Status:", classes="form-label")
                    with Vertical(classes="form-input"):
                        yield Select(
                            options=STATUS_OPTIONS,
                            value=status,
                            id="status-select",
                            allow_blank=False,
                        )

            with Horizontal(classes="form-row"):
                yield Label("Description:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield TextArea(text=description, id="description-input")

            yield Static("", id="form-error", classes="error-text")

            with Horizontal(classes="button-row"):
                button_text = "Update" if self.project_id else "Create"
                yield Button(button_text, variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_data(self) -> None:
        """Load data from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.company import list_companies
            from taskyn.core.project import get_project

            with get_db() as db:
                self._companies = list_companies(db)
                if self.project_id:
                    self._project = get_project(db, self.project_id)
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
        self._submit_form()

    def _submit_form(self) -> None:
        """Validate and submit the form."""
        company_id = self.query_one("#company-select", Select).value
        name = self.query_one("#name-input", Input).value.strip()
        methodology = self.query_one("#methodology-select", Select).value
        description = self.query_one("#description-input", TextArea).text.strip()

        error_display = self.query_one("#form-error", Static)

        if not company_id or company_id == Select.BLANK:
            error_display.update("Company is required")
            return

        if not name:
            error_display.update("Name is required")
            self.query_one("#name-input", Input).focus()
            return

        error_display.update("")

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import create_project, update_project

            with get_db() as db:
                if self.project_id:
                    status = self.query_one("#status-select", Select).value
                    update_project(
                        db,
                        self.project_id,
                        name=name,
                        description=description if description else None,
                        status=status,
                    )
                    self.app.notify(f"Updated: {name}", title="Project Updated")
                else:
                    create_project(
                        db,
                        company_id=company_id,
                        name=name,
                        methodology=methodology,
                        description=description if description else None,
                    )
                    self.app.notify(f"Created: {name}", title="Project Created")

            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
