"""Status picker dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option


STATUS_STYLES = {
    "backlog": ("○ Backlog", "#94A3B8"),
    "todo": ("● Todo", "#8B5CF6"),
    "ready": ("● Ready", "#8B5CF6"),
    "in_progress": ("◐ In Progress", "#F59E0B"),
    "done": ("✓ Done", "#10B981"),
    "blocked": ("✗ Blocked", "#F43F5E"),
}


class StatusPickerDialog(ModalScreen[str | None]):
    """Dialog for selecting a new status."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("enter", "select", "Select", show=False),
    ]

    def __init__(self, task_id: str, current_status: str) -> None:
        """Initialize the picker.

        Args:
            task_id: ID of the task
            current_status: Current status of the task
        """
        super().__init__()
        self.task_id = task_id
        self.current_status = current_status
        self._valid_statuses: list[str] = []

    def compose(self) -> ComposeResult:
        self._load_valid_statuses()

        current_display, _ = STATUS_STYLES.get(
            self.current_status, (f"? {self.current_status}", "#888888")
        )

        with Vertical(classes="modal-dialog-narrow"):
            yield Static("Change Status", classes="dialog-title")
            yield Static(f"Current: {current_display}", classes="dialog-message")

            options = []
            for status in self._valid_statuses:
                display, color = STATUS_STYLES.get(status, (status, "#888888"))
                if status == self.current_status:
                    display = f"{display} (current)"
                options.append(Option(display, id=status))

            yield OptionList(*options, id="status-list")

    def _load_valid_statuses(self) -> None:
        """Load valid status transitions."""
        self._valid_statuses = ["backlog", "todo", "ready", "in_progress", "done", "blocked"]

        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import get_node
            from taskyn.core.workflow import get_valid_transitions

            with get_db() as db:
                task = get_node(db, self.task_id)
                if task:
                    transitions = get_valid_transitions(db, self.task_id)
                    if transitions:
                        self._valid_statuses = [self.current_status] + [
                            t for t in transitions if t != self.current_status
                        ]
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        selected_status = event.option.id
        if selected_status and selected_status != self.current_status:
            self.dismiss(selected_status)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select the highlighted option."""
        option_list = self.query_one("#status-list", OptionList)
        if option_list.highlighted is not None:
            option = option_list.get_option_at_index(option_list.highlighted)
            if option.id != self.current_status:
                self.dismiss(option.id)
            else:
                self.dismiss(None)
