"""Story form modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.validation import Length
from textual.widgets import Button, Input, Label, Select, Static, TextArea


PRIORITY_OPTIONS = [
    ("High", "high"),
    ("Medium", "medium"),
    ("Low", "low"),
]


class StoryFormModal(ModalScreen[bool]):
    """Modal dialog for creating or editing a story."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        story_id: str | None = None,
        project_id: str | None = None,
        milestone_id: str | None = None,
    ) -> None:
        """Initialize the modal.

        Args:
            story_id: ID of story to edit (None for new story)
            project_id: Default project for new story
            milestone_id: Default milestone for new story
        """
        super().__init__()
        self.story_id = story_id
        self.default_project_id = project_id
        self.default_milestone_id = milestone_id
        self._story = None
        self._projects: list[tuple[str, str]] = []
        self._milestones: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        self._load_projects()
        self._load_milestones()

        title_val = ""
        description = ""
        story_points = ""
        acceptance_criteria = ""
        priority = "medium"
        project_id = self.default_project_id
        milestone_id = self.default_milestone_id

        if self.story_id:
            self._load_story()
            if self._story:
                title_val = self._story.title
                description = self._story.description or ""
                story_points = str(self._story.story_points) if self._story.story_points else ""
                priority = self._story.priority or "medium"
                project_id = self._story.project_id
                milestone_id = self._story.milestone_id
                props = self._story.properties or {}
                acceptance_criteria = props.get("acceptance_criteria", "")

        dialog_title = "Edit Story" if self.story_id else "Create New Story"

        with Vertical(classes="modal-dialog-wide"):
            yield Static(dialog_title, classes="dialog-title")

            with Horizontal(classes="form-row"):
                yield Label("Title:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Input(
                        value=title_val,
                        placeholder="Story title",
                        id="title-input",
                        validators=[Length(minimum=1, maximum=200)],
                    )

            with Horizontal(classes="form-row"):
                yield Label("Project:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Select(
                        options=self._projects,
                        value=project_id if project_id else Select.BLANK,
                        allow_blank=True,
                        id="project-select",
                    )

            with Horizontal(classes="form-row"):
                yield Label("Milestone:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Select(
                        options=self._milestones,
                        value=milestone_id if milestone_id else Select.BLANK,
                        allow_blank=True,
                        id="milestone-select",
                    )

            with Horizontal(classes="form-row"):
                yield Label("Priority:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Select(
                        options=PRIORITY_OPTIONS,
                        value=priority,
                        id="priority-select",
                    )

            with Horizontal(classes="form-row"):
                yield Label("Story Points:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield Input(
                        value=story_points,
                        placeholder="1, 2, 3, 5, 8, 13...",
                        id="points-input",
                    )

            with Horizontal(classes="form-row"):
                yield Label("Description:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield TextArea(text=description, id="description-input")

            with Horizontal(classes="form-row"):
                yield Label("Acceptance\nCriteria:", classes="form-label")
                with Vertical(classes="form-input"):
                    yield TextArea(text=acceptance_criteria, id="acceptance-input")

            yield Static("", id="form-error", classes="error-text")

            with Horizontal(classes="button-row"):
                button_text = "Update" if self.story_id else "Create"
                yield Button(button_text, variant="primary", id="submit-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_projects(self) -> None:
        """Load project options from database."""
        self._projects = [("(No Project)", "")]
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import list_projects

            with get_db() as db:
                projects = list_projects(db)
                for project in sorted(projects, key=lambda p: p.name):
                    self._projects.append((project.name, project.id))
        except Exception:
            pass

    def _load_milestones(self) -> None:
        """Load milestone options from database."""
        self._milestones = [("(No Milestone)", "")]
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.milestone import list_milestones

            with get_db() as db:
                milestones = list_milestones(db)
                for ms in sorted(milestones, key=lambda m: m.name):
                    self._milestones.append((ms.name, ms.id))
        except Exception:
            pass

    def _load_story(self) -> None:
        """Load story data from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import get_node

            with get_db() as db:
                self._story = get_node(db, self.story_id)
        except Exception:
            pass

    def on_mount(self) -> None:
        """Focus the title input when mounted."""
        self.query_one("#title-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self._submit_form()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        if event.input.id == "title-input":
            self.query_one("#project-select", Select).focus()
        elif event.input.id == "points-input":
            self.query_one("#description-input", TextArea).focus()

    def _submit_form(self) -> None:
        """Validate and submit the form."""
        title = self.query_one("#title-input", Input).value.strip()
        project_id = self.query_one("#project-select", Select).value
        milestone_id = self.query_one("#milestone-select", Select).value
        priority = self.query_one("#priority-select", Select).value
        points_str = self.query_one("#points-input", Input).value.strip()
        description = self.query_one("#description-input", TextArea).text.strip()
        acceptance = self.query_one("#acceptance-input", TextArea).text.strip()

        error_display = self.query_one("#form-error", Static)

        if not title:
            error_display.update("Title is required")
            self.query_one("#title-input", Input).focus()
            return

        if not project_id or project_id == Select.BLANK:
            error_display.update("Project is required")
            self.query_one("#project-select", Select).focus()
            return

        story_points = None
        if points_str:
            try:
                story_points = int(points_str)
                if story_points < 0:
                    raise ValueError("Must be positive")
            except ValueError:
                error_display.update("Story points must be a positive number")
                self.query_one("#points-input", Input).focus()
                return

        if milestone_id == Select.BLANK:
            milestone_id = None

        error_display.update("")

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.work_items import create_story
            from taskyn.graph.nodes import update_node

            with get_db() as db:
                if self.story_id:
                    properties = {"acceptance_criteria": acceptance} if acceptance else None
                    update_node(
                        db,
                        self.story_id,
                        title=title,
                        description=description if description else None,
                        story_points=story_points,
                        priority=priority,
                        milestone_id=milestone_id,
                        properties=properties,
                    )
                    self.app.notify(f"Updated: {title}", title="Story Updated")
                else:
                    create_story(
                        db,
                        project_id=project_id,
                        title=title,
                        description=description if description else None,
                        milestone_id=milestone_id,
                        priority=priority,
                        story_points=story_points,
                        acceptance_criteria=acceptance if acceptance else None,
                    )
                    self.app.notify(f"Created: {title}", title="Story Created")

            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
