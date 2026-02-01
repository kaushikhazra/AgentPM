"""Confirmation dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen[bool]):
    """Generic confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #confirm-dialog {
        width: 50;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }

    #confirm-dialog.warning {
        border: thick $warning;
    }

    #confirm-dialog.info {
        border: thick $primary;
    }

    #confirm-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #confirm-title.destructive {
        color: $error;
    }

    #confirm-title.warning {
        color: $warning;
    }

    #confirm-title.info {
        color: $primary;
    }

    #confirm-message {
        text-align: center;
        padding: 1 0;
    }

    #confirm-buttons {
        align: center middle;
        padding-top: 1;
    }

    #confirm-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        message: str,
        title: str = "Confirm",
        confirm_label: str = "Yes",
        cancel_label: str = "No",
        destructive: bool = False,
    ) -> None:
        """Initialize the dialog.

        Args:
            message: Message to display
            title: Dialog title
            confirm_label: Label for confirm button
            cancel_label: Label for cancel button
            destructive: If True, style as destructive action
        """
        super().__init__()
        self.message = message
        self.dialog_title = title
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.destructive = destructive

    def compose(self) -> ComposeResult:
        dialog_class = ""
        title_class = ""

        if self.destructive:
            title_class = "destructive"
        else:
            dialog_class = "info"
            title_class = "info"

        with Vertical(id="confirm-dialog", classes=dialog_class):
            yield Static(self.dialog_title, id="confirm-title", classes=title_class)
            yield Static(self.message, id="confirm-message")

            with Horizontal(id="confirm-buttons"):
                variant = "error" if self.destructive else "primary"
                yield Button(self.confirm_label, variant=variant, id="confirm-yes")
                yield Button(self.cancel_label, variant="default", id="confirm-no")

    def on_mount(self) -> None:
        """Focus the No button by default for destructive actions."""
        if self.destructive:
            self.query_one("#confirm-no", Button).focus()
        else:
            self.query_one("#confirm-yes", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "confirm-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        """Confirm action."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel action."""
        self.dismiss(False)
