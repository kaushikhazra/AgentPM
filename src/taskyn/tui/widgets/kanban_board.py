"""Kanban board widget."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from taskyn.tui.widgets.task_card import TaskCard


# Column definitions
KANBAN_COLUMNS = [
    ("backlog", "Backlog", "#94A3B8"),
    ("todo", "Todo", "#8B5CF6"),
    ("in_progress", "In Progress", "#F59E0B"),
    ("done", "Done", "#10B981"),
]


class KanbanColumn(Vertical):
    """A single column in the Kanban board."""

    DEFAULT_CSS = """
    KanbanColumn {
        width: 1fr;
        height: 100%;
        margin: 0 1;
        border: solid $surface-lighten-1;
        background: $surface-darken-1;
    }

    KanbanColumn .column-header {
        height: 3;
        padding: 1;
        text-align: center;
        text-style: bold;
        border-bottom: solid $surface-lighten-1;
    }

    KanbanColumn .column-count {
        text-align: center;
        color: $text-muted;
        padding-bottom: 1;
    }

    KanbanColumn .column-content {
        padding: 1;
    }

    KanbanColumn .empty-message {
        text-align: center;
        color: $text-muted;
        padding: 2;
    }
    """

    status: reactive[str] = reactive("")
    count: reactive[int] = reactive(0)

    def __init__(self, status: str, title: str, color: str) -> None:
        super().__init__(id=f"column-{status}")
        self.status = status
        self._title = title
        self._color = color

    def compose(self) -> ComposeResult:
        yield Static(
            f"[{self._color}]{self._title}[/]",
            classes="column-header",
        )
        yield Static("0 tasks", id=f"count-{self.status}", classes="column-count")
        yield VerticalScroll(id=f"content-{self.status}", classes="column-content")

    def add_task(self, task_card: TaskCard) -> None:
        """Add a task card to this column."""
        content = self.query_one(f"#content-{self.status}", VerticalScroll)
        content.mount(task_card)
        self.count += 1
        self._update_count()

    def clear_tasks(self) -> None:
        """Remove all task cards."""
        content = self.query_one(f"#content-{self.status}", VerticalScroll)
        content.remove_children()
        self.count = 0
        self._update_count()

    def _update_count(self) -> None:
        """Update the count display."""
        count_label = self.query_one(f"#count-{self.status}", Static)
        count_label.update(f"{self.count} task{'s' if self.count != 1 else ''}")


class KanbanBoard(Horizontal):
    """Kanban board with status columns."""

    DEFAULT_CSS = """
    KanbanBoard {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("left", "move_left", "Move Left", show=False),
        Binding("right", "move_right", "Move Right", show=False),
        Binding("h", "move_left", "Move Left", show=False),
        Binding("l", "move_right", "Move Right", show=False),
    ]

    def __init__(self) -> None:
        super().__init__(id="kanban-board")
        self._current_column = 0

    def compose(self) -> ComposeResult:
        for status, title, color in KANBAN_COLUMNS:
            yield KanbanColumn(status, title, color)

    def on_mount(self) -> None:
        """Load tasks into columns."""
        self.refresh_board()

    def refresh_board(self) -> None:
        """Refresh all columns from database."""
        # Clear existing tasks
        for status, _, _ in KANBAN_COLUMNS:
            column = self.query_one(f"#column-{status}", KanbanColumn)
            column.clear_tasks()

        # Load tasks
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                nodes = list_nodes(db)
                tasks = [n for n in nodes if n.node_type in ("task", "story")]

                for task in tasks:
                    # Determine column
                    status = task.status
                    if status == "ready":
                        status = "todo"

                    # Skip blocked tasks for now
                    if status == "blocked":
                        status = "backlog"

                    # Get metadata
                    metadata = task.metadata or {}
                    priority = metadata.get("priority", "medium")
                    due_date = metadata.get("due_date", "")

                    # Format due date
                    if due_date:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(due_date)
                            due_date = dt.strftime("%b %d")
                        except (ValueError, TypeError):
                            due_date = due_date[:10] if len(due_date) > 10 else due_date

                    # Create card
                    card = TaskCard(
                        task_id=task.id,
                        title=task.title,
                        status=status,
                        priority=priority,
                        due_date=due_date,
                    )

                    # Add to column
                    try:
                        column = self.query_one(f"#column-{status}", KanbanColumn)
                        column.add_task(card)
                    except Exception:
                        # Fallback to backlog
                        column = self.query_one("#column-backlog", KanbanColumn)
                        column.add_task(card)

        except Exception:
            pass

    def on_task_card_selected(self, event: TaskCard.Selected) -> None:
        """Handle card selection."""
        from taskyn.tui.screens.task_detail import TaskDetailScreen

        self.app.push_screen(TaskDetailScreen(event.task_id))

    def on_task_card_edit_requested(self, event: TaskCard.EditRequested) -> None:
        """Handle edit request."""
        self.app.open_edit_task(event.task_id)

    def on_task_card_status_change_requested(
        self, event: TaskCard.StatusChangeRequested
    ) -> None:
        """Handle status change request."""
        self.app.open_status_picker(event.task_id, event.current_status)

    def action_move_left(self) -> None:
        """Move focus to left column."""
        if self._current_column > 0:
            self._current_column -= 1
            self._focus_column()

    def action_move_right(self) -> None:
        """Move focus to right column."""
        if self._current_column < len(KANBAN_COLUMNS) - 1:
            self._current_column += 1
            self._focus_column()

    def _focus_column(self) -> None:
        """Focus the first card in current column."""
        status = KANBAN_COLUMNS[self._current_column][0]
        try:
            content = self.query_one(f"#content-{status}", VerticalScroll)
            cards = list(content.query(TaskCard))
            if cards:
                cards[0].focus()
        except Exception:
            pass
