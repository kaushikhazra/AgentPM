"""Company form modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Static, TextArea


class CompanyFormModal(ModalScreen[bool]):
    """Modal dialog for creating or editing a company."""

    DEFAULT_CSS = """
    CompanyFormModal {
        align: center middle;
    }

    #company-form-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #company-form-title {
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
        width: 12;
        padding-top: 1;
    }

    .form-input {
        width: 1fr;
    }

    Input {
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

    def __init__(self, company_id: str | None = None) -> None:
        """Initialize the modal.

        Args:
            company_id: ID of company to edit (None for new company)
        """
        super().__init__()
        self.company_id = company_id
        self._company = None

    def compose(self) -> ComposeResult:
        # Load existing data if editing
        name = ""
        description = ""

        if self.company_id:
            self._load_company()
            if self._company:
                name = self._company.name
                description = self._company.description or ""

        title = "Edit Company" if self.company_id else "Create New Company"

        with Vertical(id="company-form-dialog"):
            yield Static(title, id="company-form-title")

            # Name field
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    value=name,
                    placeholder="Company name",
                    id="name-input",
                    validators=[Length(minimum=1, maximum=100)],
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
                button_text = "Update" if self.company_id else "Create"
                yield Button(button_text, variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_company(self) -> None:
        """Load company data from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.company import get_company

            with get_db() as db:
                self._company = get_company(db, self.company_id)
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
        description = self.query_one("#description-input", TextArea).text.strip()

        error_display = self.query_one("#form-error", Static)

        if not name:
            error_display.update("Name is required")
            self.query_one("#name-input", Input).focus()
            return

        error_display.update("")

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.company import create_company, update_company

            with get_db() as db:
                if self.company_id:
                    # Update existing
                    update_company(
                        db,
                        self.company_id,
                        name=name,
                        description=description if description else None,
                    )
                    self.app.notify(f"Updated: {name}", title="Company Updated")
                else:
                    # Create new
                    create_company(
                        db,
                        name=name,
                        description=description if description else None,
                    )
                    self.app.notify(f"Created: {name}", title="Company Created")

            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
