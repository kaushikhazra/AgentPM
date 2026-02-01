"""New task modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from taskyn.tui.widgets.task_form import TaskForm


class NewTaskModal(ModalScreen[bool]):
    """Modal dialog for creating a new task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, project_id: str | None = None) -> None:
        """Initialize the modal.

        Args:
            project_id: Pre-select this project in the form
        """
        super().__init__()
        self.project_id = project_id

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog-wide"):
            yield Static("Create New Task", classes="dialog-title")
            yield TaskForm(project_id=self.project_id)

    def on_mount(self) -> None:
        """Focus the title input when mounted."""
        form = self.query_one(TaskForm)
        form.focus_title()

    def on_task_form_submitted(self, event: TaskForm.Submitted) -> None:
        """Handle form submission."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import create_node
            from taskyn.graph.edges import create_edge

            data = event.data
            project_id = data.pop("project_id", None)

            with get_db() as db:
                node = create_node(
                    db,
                    node_type=data["node_type"],
                    title=data["title"],
                    status=data.get("status", "backlog"),
                    description=data.get("description"),
                    metadata=data.get("metadata"),
                )

                if project_id:
                    try:
                        create_edge(db, project_id, node.id, "parent")
                    except Exception:
                        pass

            self.app.notify(f"Created: {node.title}", title="Task Created")
            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def on_task_form_cancelled(self, event: TaskForm.Cancelled) -> None:
        """Handle form cancellation."""
        self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
