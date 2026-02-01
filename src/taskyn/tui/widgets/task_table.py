"""Task table widget for Taskyn TUI."""

from textual.message import Message
from textual.widgets import DataTable


# Status display
STATUS_DISPLAY = {
    "backlog": ("○", "status-backlog"),
    "todo": ("●", "status-todo"),
    "ready": ("●", "status-ready"),
    "in_progress": ("◐", "status-in_progress"),
    "done": ("✓", "status-done"),
    "blocked": ("✗", "status-blocked"),
}

# Priority display
PRIORITY_DISPLAY = {
    "high": ("▲", "priority-high"),
    "medium": ("─", "priority-medium"),
    "low": ("▼", "priority-low"),
}


class TaskTable(DataTable):
    """Table displaying tasks with status, title, priority, and due date."""

    class TaskSelected(Message):
        """Posted when a task is selected."""

        def __init__(self, task_id: str, task_title: str) -> None:
            super().__init__()
            self.task_id = task_id
            self.task_title = task_title

    def __init__(self) -> None:
        super().__init__(id="task-table")
        self._task_ids: dict[str, str] = {}  # row_key -> task_id

    def on_mount(self) -> None:
        """Initialize table columns and load data."""
        self.cursor_type = "row"
        self.zebra_stripes = True

        # Add columns
        self.add_column("Status", width=10, key="status")
        self.add_column("Title", width=None, key="title")  # Flexible width
        self.add_column("Priority", width=10, key="priority")
        self.add_column("Due", width=12, key="due")

        self.load_tasks()

    def load_tasks(self, project_id: str | None = None) -> None:
        """Load tasks from database."""
        self.clear()
        self._task_ids.clear()

        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                nodes = list_nodes(db)

                # Filter to tasks and stories
                tasks = [n for n in nodes if n.node_type in ("task", "story")]

                # Sort: in_progress first, then todo, then backlog, done last
                status_order = {
                    "in_progress": 0,
                    "todo": 1,
                    "ready": 1,
                    "backlog": 2,
                    "blocked": 3,
                    "done": 4,
                }
                tasks.sort(key=lambda t: (status_order.get(t.status, 99), t.title))

                for task in tasks:
                    self._add_task_row(task)

        except Exception:
            # Database might not exist yet
            pass

    def _add_task_row(self, task) -> None:
        """Add a task to the table."""
        # Status cell
        status_icon, status_class = STATUS_DISPLAY.get(
            task.status, ("?", "status-backlog")
        )
        status_text = f"{status_icon} {task.status.upper()[:4]}"

        # Priority cell
        priority = task.metadata.get("priority", "medium") if task.metadata else "medium"
        priority_icon, priority_class = PRIORITY_DISPLAY.get(
            priority, ("─", "priority-medium")
        )
        priority_text = f"{priority_icon} {priority.upper()[:3]}"

        # Due date cell
        due_date = task.metadata.get("due_date", "") if task.metadata else ""
        if due_date:
            # Format as short date
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(due_date)
                due_text = dt.strftime("%b %d")
            except (ValueError, TypeError):
                due_text = due_date[:10] if len(due_date) > 10 else due_date
        else:
            due_text = ""

        # Title (truncate if needed)
        title = task.title
        if len(title) > 40:
            title = title[:37] + "..."

        # Add row
        row_key = f"task-{task.id}"
        self.add_row(
            status_text,
            title,
            priority_text,
            due_text,
            key=row_key,
        )
        self._task_ids[row_key] = task.id

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        row_key = str(event.row_key.value) if event.row_key else None
        if row_key and row_key in self._task_ids:
            task_id = self._task_ids[row_key]
            # Get title from the row
            row_idx = event.cursor_row
            title = str(self.get_cell_at((row_idx, 1)))
            self.post_message(self.TaskSelected(task_id, title))

    def filter_by_project(self, project_id: str | None) -> None:
        """Filter tasks to a specific project."""
        # TODO: Implement project filtering
        self.load_tasks(project_id)

    def refresh_tasks(self) -> None:
        """Refresh tasks from database."""
        self.load_tasks()
