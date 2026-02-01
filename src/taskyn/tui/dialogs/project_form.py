"""Project form modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Select, Static, TextArea


# Methodology options
METHODOLOGY_OPTIONS = [
    ("Classic Agile", "classic_agile"),
    ("Spec Driven", "spec_driven"),
]

# Project status options
STATUS_OPTIONS = [
    ("Active", "active"),
    ("On Hold", "on_hold"),
    ("Completed", "completed"),
    ("Archived", "archived"),
]


class ProjectFormModal(ModalScreen[bool]):
    """Modal dialog for creating or editing a project."""

    DEFAULT_CSS = """
    ProjectFormModal {
        align: center middle;
    }

    #project-form-dialog {
        width: 70;
        height: auto;
        max-height: 85%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #project-form-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    .form-row {
        height: auto;
        margin-bottom: 1;
    }

    .form-label {
        width: 14;
        padding-top: 1;
    }

    .form-input {
        width: 1fr;
    }

    Input {
        width: 100%;
    }

    Select {
        width: 100%;
    }

    TextArea {
        height: 4;
        width: 100%;
    }

    .button-row {
        margin-top: 1;
        height: auto;
        align: center middle;
    }

    .button-row Button {
        margin: 0 1;
    }

    .error-text {
        color: $error;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        project_id: str | None = None,
        company_id: str | None = None,
    ) -> None:
        """Initialize the modal.

        Args:
            project_id: ID of project to edit (None for new project)
            company_id: Default company for new project
        """
        super().__init__()
        self.project_id = project_id
        self.default_company_id = company_id
        self._project = None
        self._companies: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        # Load companies and existing data
        self._load_companies()

        name = ""
        description = ""
        methodology = "classic_agile"
        status = "active"
        company_id = self.default_company_id

        if self.project_id:
            self._load_project()
            if self._project:
                name = self._project.name
                description = self._project.description or ""
                methodology = self._project.methodology
                status = self._project.status
                company_id = self._project.company_id

        title = "Edit Project" if self.project_id else "Create New Project"

        with Vertical(id="project-form-dialog"):
            yield Static(title, id="project-form-title")

            # Name field
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    value=name,
                    placeholder="Project name",
                    id="name-input",
                    validators=[Length(minimum=1, maximum=100)],
                    classes="form-input",
                )

            # Company field
            with Horizontal(classes="form-row"):
                yield Label("Company:", classes="form-label")
                yield Select(
                    options=self._companies,
                    value=company_id if company_id else Select.BLANK,
                    allow_blank=True,
                    id="company-select",
                    classes="form-input",
                )

            # Methodology field (only for new projects)
            if not self.project_id:
                with Horizontal(classes="form-row"):
                    yield Label("Methodology:", classes="form-label")
                    yield Select(
                        options=METHODOLOGY_OPTIONS,
                        value=methodology,
                        id="methodology-select",
                        classes="form-input",
                    )
            else:
                # Show status for existing projects
                with Horizontal(classes="form-row"):
                    yield Label("Status:", classes="form-label")
                    yield Select(
                        options=STATUS_OPTIONS,
                        value=status,
                        id="status-select",
                        classes="form-input",
                    )

            # Description field
            with Horizontal(classes="form-row"):
                yield Label("Description:", classes="form-label")
                yield TextArea(
                    text=description,
                    id="description-input",
                    classes="form-input",
                )

            # Error display
            yield Static("", id="form-error", classes="error-text")

            # Buttons
            with Horizontal(classes="button-row"):
                button_text = "Update" if self.project_id else "Create"
                yield Button(button_text, variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_companies(self) -> None:
        """Load company options from database."""
        self._companies = [("(No Company)", "")]

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.company import list_companies

            with get_db() as db:
                companies = list_companies(db)
                for company in companies:
                    self._companies.append((company.name, company.id))

        except Exception:
            pass

    def _load_project(self) -> None:
        """Load project data from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import get_project

            with get_db() as db:
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
        name = self.query_one("#name-input", Input).value.strip()
        company_id = self.query_one("#company-select", Select).value
        description = self.query_one("#description-input", TextArea).text.strip()

        error_display = self.query_one("#form-error", Static)

        if not name:
            error_display.update("Name is required")
            self.query_one("#name-input", Input).focus()
            return

        if not company_id or company_id == Select.BLANK:
            error_display.update("Company is required")
            self.query_one("#company-select", Select).focus()
            return

        error_display.update("")

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import create_project, update_project

            with get_db() as db:
                if self.project_id:
                    # Update existing
                    try:
                        status_select = self.query_one("#status-select", Select)
                        status = status_select.value
                    except Exception:
                        status = None

                    update_project(
                        db,
                        self.project_id,
                        name=name,
                        description=description if description else None,
                        status=status,
                    )
                    self.app.notify(f"Updated: {name}", title="Project Updated")
                else:
                    # Create new
                    methodology = self.query_one("#methodology-select", Select).value
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
