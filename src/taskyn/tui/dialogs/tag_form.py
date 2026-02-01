"""Tag form modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Select, Static


# Predefined color options
COLOR_OPTIONS = [
    ("Blue", "#3B82F6"),
    ("Green", "#10B981"),
    ("Yellow", "#F59E0B"),
    ("Red", "#EF4444"),
    ("Purple", "#8B5CF6"),
    ("Pink", "#EC4899"),
    ("Cyan", "#06B6D4"),
    ("Orange", "#F97316"),
    ("Gray", "#6B7280"),
]


class TagFormModal(ModalScreen[bool]):
    """Modal dialog for creating a tag."""

    DEFAULT_CSS = """
    TagFormModal {
        align: center middle;
    }

    #tag-form-dialog {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #tag-form-title {
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
        width: 10;
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

    .preview {
        padding: 1;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="tag-form-dialog"):
            yield Static("Create Tag", id="tag-form-title")

            # Name field
            with Horizontal(classes="form-row"):
                yield Label("Name:", classes="form-label")
                yield Input(
                    placeholder="Tag name",
                    id="name-input",
                    validators=[Length(minimum=1, maximum=50)],
                    classes="form-input",
                )

            # Color field
            with Horizontal(classes="form-row"):
                yield Label("Color:", classes="form-label")
                yield Select(
                    options=COLOR_OPTIONS,
                    value="#3B82F6",
                    id="color-select",
                    classes="form-input",
                )

            # Preview
            yield Static("[#3B82F6]● sample-tag[/]", id="tag-preview", classes="preview")

            # Error display
            yield Static("", id="form-error", classes="error-text")

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Create", variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        """Focus the name input when mounted."""
        self.query_one("#name-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update preview when name changes."""
        if event.input.id == "name-input":
            self._update_preview()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Update preview when color changes."""
        if event.select.id == "color-select":
            self._update_preview()

    def _update_preview(self) -> None:
        """Update the tag preview."""
        name = self.query_one("#name-input", Input).value.strip() or "sample-tag"
        color = self.query_one("#color-select", Select).value
        preview = self.query_one("#tag-preview", Static)
        preview.update(f"[{color}]● {name}[/]")

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
        color = self.query_one("#color-select", Select).value

        error_display = self.query_one("#form-error", Static)

        if not name:
            error_display.update("Name is required")
            self.query_one("#name-input", Input).focus()
            return

        error_display.update("")

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import create_tag, get_tag_by_name

            with get_db() as db:
                # Check if tag already exists
                existing = get_tag_by_name(db, name)
                if existing:
                    error_display.update("Tag already exists")
                    return

                create_tag(db, name=name, color=color)

            self.app.notify(f"Created tag: {name}", title="Tag Created")
            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
