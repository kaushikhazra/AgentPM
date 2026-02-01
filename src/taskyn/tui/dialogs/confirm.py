"""Confirmation dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen[bool]):
    """Generic confirmation dialog."""

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
        dialog_classes = "modal-dialog-narrow"
        title_classes = "dialog-title"

        if self.destructive:
            dialog_classes += " modal-dialog-destructive"
            title_classes += " dialog-title-destructive"

        with Vertical(classes=dialog_classes):
            yield Static(self.dialog_title, classes=title_classes)
            yield Static(self.message, classes="dialog-message")

            with Horizontal(classes="button-row"):
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
