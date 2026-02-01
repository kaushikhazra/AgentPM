"""Edit task modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from taskyn.tui.widgets.task_form import TaskForm


class EditTaskModal(ModalScreen[bool]):
    """Modal dialog for editing an existing task."""

    DEFAULT_CSS = """
    EditTaskModal {
        align: center middle;
    }

    #edit-task-dialog {
        width: 70;
        height: auto;
        max-height: 90%;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }

    #edit-task-title {
        text-align: center;
        text-style: bold;
        color: $warning;
        padding-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, task_id: str) -> None:
        """Initialize the modal.

        Args:
            task_id: ID of the task to edit
        """
        super().__init__()
        self.task_id = task_id
        self._initial_data: dict = {}

    def compose(self) -> ComposeResult:
        # Load task data
        self._load_task_data()

        with Vertical(id="edit-task-dialog"):
            yield Static("Edit Task", id="edit-task-title")
            yield TaskForm(task_id=self.task_id, initial_data=self._initial_data)

    def _load_task_data(self) -> None:
        """Load task data from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import get_node
            from taskyn.graph.edges import get_parents

            with get_db() as db:
                task = get_node(db, self.task_id)
                if task:
                    self._initial_data = {
                        "title": task.title,
                        "node_type": task.node_type,
                        "status": task.status,
                        "description": task.description or "",
                        "priority": (task.metadata or {}).get("priority", "medium"),
                        "due_date": (task.metadata or {}).get("due_date", ""),
                        "estimate": (task.metadata or {}).get("estimate", ""),
                    }

                    # Get parent project
                    parent_edges = get_parents(db, self.task_id, "parent")
                    if parent_edges:
                        self._initial_data["project_id"] = parent_edges[0].from_node_id

        except Exception:
            pass

    def on_mount(self) -> None:
        """Focus the title input when mounted."""
        form = self.query_one(TaskForm)
        form.focus_title()

    def on_task_form_submitted(self, event: TaskForm.Submitted) -> None:
        """Handle form submission."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import update_node

            data = event.data
            data.pop("project_id", None)  # Don't update parent here
            data.pop("task_id", None)

            with get_db() as db:
                update_node(
                    db,
                    node_id=self.task_id,
                    title=data.get("title"),
                    status=data.get("status"),
                    description=data.get("description"),
                    metadata=data.get("metadata"),
                )

            self.app.notify(f"Updated: {data['title']}", title="Task Updated")
            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def on_task_form_cancelled(self, event: TaskForm.Cancelled) -> None:
        """Handle form cancellation."""
        self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
