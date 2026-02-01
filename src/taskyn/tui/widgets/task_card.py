"""Task card widget for Kanban board."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


# Priority display
PRIORITY_ICONS = {
    "high": ("▲", "#F43F5E"),
    "medium": ("─", "#F59E0B"),
    "low": ("▼", "#94A3B8"),
}


class TaskCard(Vertical, can_focus=True):
    """Compact task card for Kanban board."""

    DEFAULT_CSS = """
    TaskCard {
        height: auto;
        min-height: 3;
        max-height: 5;
        margin: 0 0 1 0;
        padding: 0 1;
        border: solid $surface-lighten-1;
        background: $surface;
    }

    TaskCard:focus {
        border: solid $accent;
        background: $surface-lighten-1;
    }

    TaskCard:hover {
        background: $surface-lighten-1;
    }

    TaskCard .card-title {
        width: 100%;
        text-style: bold;
    }

    TaskCard .card-meta {
        width: 100%;
        color: $text-muted;
    }

    TaskCard.done .card-title {
        text-style: strike;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("enter", "select", "Open", show=False),
        Binding("e", "edit", "Edit", show=False),
        Binding("s", "status", "Status", show=False),
    ]

    task_id: reactive[str] = reactive("")
    task_title: reactive[str] = reactive("")
    task_status: reactive[str] = reactive("")
    task_priority: reactive[str] = reactive("medium")
    task_due: reactive[str] = reactive("")

    class Selected(Message):
        """Posted when card is selected."""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class EditRequested(Message):
        """Posted when edit is requested."""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class StatusChangeRequested(Message):
        """Posted when status change is requested."""

        def __init__(self, task_id: str, current_status: str) -> None:
            super().__init__()
            self.task_id = task_id
            self.current_status = current_status

    def __init__(
        self,
        task_id: str,
        title: str,
        status: str,
        priority: str = "medium",
        due_date: str = "",
    ) -> None:
        super().__init__()
        self.task_id = task_id
        self.task_title = title
        self.task_status = status
        self.task_priority = priority
        self.task_due = due_date

        if status == "done":
            self.add_class("done")

    def compose(self) -> ComposeResult:
        # Truncate title if needed
        title = self.task_title
        if len(title) > 25:
            title = title[:22] + "..."

        yield Static(title, classes="card-title")

        # Meta line with priority and due date
        priority_icon, priority_color = PRIORITY_ICONS.get(
            self.task_priority, ("─", "#F59E0B")
        )
        meta_parts = [f"[{priority_color}]{priority_icon}[/]"]

        if self.task_due:
            meta_parts.append(self.task_due)

        yield Static(" ".join(meta_parts), classes="card-meta")

    def action_select(self) -> None:
        """Open task detail."""
        self.post_message(self.Selected(self.task_id))

    def action_edit(self) -> None:
        """Request edit."""
        self.post_message(self.EditRequested(self.task_id))

    def action_status(self) -> None:
        """Request status change."""
        self.post_message(self.StatusChangeRequested(self.task_id, self.task_status))
