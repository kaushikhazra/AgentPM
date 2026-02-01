"""Task form widget for creating/editing tasks."""

from datetime import datetime
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.validation import Length, Regex
from textual.widgets import Button, Input, Label, Select, Static, TextArea


# Priority options
PRIORITY_OPTIONS = [
    ("High", "high"),
    ("Medium", "medium"),
    ("Low", "low"),
]

# Node type options
TYPE_OPTIONS = [
    ("Task", "task"),
    ("Story", "story"),
]


class TaskForm(Vertical):
    """Form for creating or editing a task."""

    DEFAULT_CSS = """
    TaskForm {
        padding: 1 2;
        height: auto;
    }

    TaskForm .form-row {
        height: auto;
        margin-bottom: 1;
    }

    TaskForm .form-label {
        width: 12;
        padding-top: 1;
    }

    TaskForm .form-input {
        width: 1fr;
    }

    TaskForm Input {
        width: 100%;
    }

    TaskForm Select {
        width: 100%;
    }

    TaskForm TextArea {
        height: 6;
        width: 100%;
    }

    TaskForm .button-row {
        margin-top: 1;
        height: auto;
        align: center middle;
    }

    TaskForm Button {
        margin: 0 1;
    }

    TaskForm .error-text {
        color: #F43F5E;
        height: auto;
    }
    """

    class Submitted(Message):
        """Posted when form is submitted."""

        def __init__(self, data: dict[str, Any]) -> None:
            super().__init__()
            self.data = data

    class Cancelled(Message):
        """Posted when form is cancelled."""

        pass

    def __init__(
        self,
        task_id: str | None = None,
        initial_data: dict[str, Any] | None = None,
        project_id: str | None = None,
    ) -> None:
        """Initialize the form.

        Args:
            task_id: ID of task being edited (None for new task)
            initial_data: Pre-populate form with this data
            project_id: Default project ID for new tasks
        """
        super().__init__()
        self.task_id = task_id
        self.initial_data = initial_data or {}
        self.default_project_id = project_id
        self._projects: list[tuple[str, str]] = []
        self._statuses: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        # Load options
        self._load_projects()
        self._load_statuses()

        # Title
        with Horizontal(classes="form-row"):
            yield Label("Title:", classes="form-label")
            yield Input(
                value=self.initial_data.get("title", ""),
                placeholder="Enter task title",
                id="title-input",
                validators=[Length(minimum=1, maximum=200)],
                classes="form-input",
            )

        # Project and Type row
        with Horizontal(classes="form-row"):
            yield Label("Project:", classes="form-label")
            default_project = self.initial_data.get("project_id", self.default_project_id)
            yield Select(
                options=self._projects,
                value=default_project,
                id="project-select",
                classes="form-input",
            )

        with Horizontal(classes="form-row"):
            yield Label("Type:", classes="form-label")
            yield Select(
                options=TYPE_OPTIONS,
                value=self.initial_data.get("node_type", "task"),
                id="type-select",
                classes="form-input",
            )

        # Priority and Status row
        with Horizontal(classes="form-row"):
            yield Label("Priority:", classes="form-label")
            yield Select(
                options=PRIORITY_OPTIONS,
                value=self.initial_data.get("priority", "medium"),
                id="priority-select",
                classes="form-input",
            )

        with Horizontal(classes="form-row"):
            yield Label("Status:", classes="form-label")
            yield Select(
                options=self._statuses,
                value=self.initial_data.get("status", "backlog"),
                id="status-select",
                classes="form-input",
            )

        # Description
        with Horizontal(classes="form-row"):
            yield Label("Description:", classes="form-label")
            yield TextArea(
                text=self.initial_data.get("description", ""),
                id="description-input",
                classes="form-input",
            )

        # Due date and Estimate row
        with Horizontal(classes="form-row"):
            yield Label("Due Date:", classes="form-label")
            yield Input(
                value=self.initial_data.get("due_date", ""),
                placeholder="YYYY-MM-DD",
                id="due-date-input",
                validators=[Regex(r"^$|^\d{4}-\d{2}-\d{2}$")],
                classes="form-input",
            )

        with Horizontal(classes="form-row"):
            yield Label("Estimate:", classes="form-label")
            yield Input(
                value=self.initial_data.get("estimate", ""),
                placeholder="e.g. 2h, 30m, 1d",
                id="estimate-input",
                classes="form-input",
            )

        # Error display
        yield Static("", id="form-error", classes="error-text")

        # Buttons
        with Horizontal(classes="button-row"):
            button_text = "Update Task" if self.task_id else "Create Task"
            yield Button(button_text, variant="primary", id="submit-btn")
            yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_projects(self) -> None:
        """Load project options from database."""
        self._projects = [("(No Project)", "")]

        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                nodes = list_nodes(db)
                projects = [n for n in nodes if n.node_type == "project"]
                projects.sort(key=lambda p: p.title)

                for proj in projects:
                    self._projects.append((proj.title, proj.id))

        except Exception:
            pass

    def _load_statuses(self) -> None:
        """Load status options for current methodology."""
        # Default to classic agile statuses
        self._statuses = [
            ("Backlog", "backlog"),
            ("Ready", "ready"),
            ("In Progress", "in_progress"),
            ("Done", "done"),
        ]

        try:
            from taskyn.db.connection import get_db
            from taskyn.methodologies import get_methodology

            with get_db() as db:
                # Try to get methodology from a project
                methodology = get_methodology(db)
                if methodology:
                    statuses = methodology.get_statuses("task")
                    if statuses:
                        self._statuses = [(s.replace("_", " ").title(), s) for s in statuses]

        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self._submit_form()
        elif event.button.id == "cancel-btn":
            self.post_message(self.Cancelled())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        # Move to next field or submit
        if event.input.id == "title-input":
            self.query_one("#project-select", Select).focus()
        elif event.input.id == "due-date-input":
            self.query_one("#estimate-input", Input).focus()
        elif event.input.id == "estimate-input":
            self._submit_form()

    def _submit_form(self) -> None:
        """Validate and submit the form."""
        # Gather values
        title = self.query_one("#title-input", Input).value.strip()
        project_id = self.query_one("#project-select", Select).value
        node_type = self.query_one("#type-select", Select).value
        priority = self.query_one("#priority-select", Select).value
        status = self.query_one("#status-select", Select).value
        description = self.query_one("#description-input", TextArea).text.strip()
        due_date = self.query_one("#due-date-input", Input).value.strip()
        estimate = self.query_one("#estimate-input", Input).value.strip()

        # Validate
        error_display = self.query_one("#form-error", Static)

        if not title:
            error_display.update("Title is required")
            self.query_one("#title-input", Input).focus()
            return

        # Validate due date format
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                error_display.update("Due date must be YYYY-MM-DD format")
                self.query_one("#due-date-input", Input).focus()
                return

        # Clear error
        error_display.update("")

        # Build data dict
        data = {
            "title": title,
            "node_type": node_type,
            "status": status,
            "description": description if description else None,
            "metadata": {
                "priority": priority,
            },
        }

        if project_id:
            data["project_id"] = project_id

        if due_date:
            data["metadata"]["due_date"] = due_date

        if estimate:
            data["metadata"]["estimate"] = estimate

        if self.task_id:
            data["task_id"] = self.task_id

        self.post_message(self.Submitted(data))

    def focus_title(self) -> None:
        """Focus the title input."""
        self.query_one("#title-input", Input).focus()
