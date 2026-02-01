"""Activity history screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Select, Static


# Entity type filter options
TYPE_OPTIONS = [
    ("All Types", ""),
    ("Tasks", "task"),
    ("Stories", "story"),
    ("Projects", "project"),
    ("Milestones", "milestone"),
    ("Companies", "company"),
]

# Action filter options
ACTION_OPTIONS = [
    ("All Actions", ""),
    ("Created", "created"),
    ("Updated", "updated"),
    ("Deleted", "deleted"),
    ("Status Changed", "status_changed"),
    ("Completed", "completed"),
]


class ActivityScreen(Screen):
    """Full activity history screen with filters."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("1", "go_dashboard", "Dashboard", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._activities = []
        self._page = 1
        self._page_size = 50
        self._total = 0

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="activity-header"):
            yield Static("Activity History", id="activity-title")

            with Horizontal(id="filter-row"):
                yield Label("Type:", classes="filter-label")
                yield Select(
                    options=TYPE_OPTIONS,
                    value="",
                    id="type-filter",
                    classes="filter-select",
                )
                yield Label("Action:", classes="filter-label")
                yield Select(
                    options=ACTION_OPTIONS,
                    value="",
                    id="action-filter",
                    classes="filter-select",
                )
                yield Button("Refresh", variant="default", id="refresh-btn")

        yield VerticalScroll(id="activity-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load activity on mount."""
        self._load_activity()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-btn":
            self._load_activity()
        elif event.button.id == "prev-btn":
            self._page = max(1, self._page - 1)
            self._load_activity()
        elif event.button.id == "next-btn":
            max_page = (self._total + self._page_size - 1) // self._page_size
            self._page = min(max_page, self._page + 1)
            self._load_activity()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Re-load when filters change."""
        self._page = 1
        self._load_activity()

    def action_refresh(self) -> None:
        """Refresh activity list."""
        self._load_activity()

    def _load_activity(self) -> None:
        """Load activity from database."""
        type_filter = self.query_one("#type-filter", Select).value
        action_filter = self.query_one("#action-filter", Select).value

        content = self.query_one("#activity-content", VerticalScroll)
        content.remove_children()

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.activity import list_activity

            with get_db() as db:
                # Get activities with filters
                all_activities = list_activity(
                    db,
                    node_type=type_filter if type_filter else None,
                    limit=500,  # Get more to filter locally
                )

                # Filter by action if specified
                if action_filter:
                    all_activities = [a for a in all_activities if a.action == action_filter]

                self._total = len(all_activities)

                # Paginate
                start = (self._page - 1) * self._page_size
                end = start + self._page_size
                self._activities = all_activities[start:end]

                self._render_activity()

        except Exception as e:
            content.mount(Static(f"[red]Error loading activity: {e}[/red]", classes="no-activity"))

    def _render_activity(self) -> None:
        """Render activity list."""
        content = self.query_one("#activity-content", VerticalScroll)
        content.remove_children()

        if not self._activities:
            content.mount(Static("No activity found", classes="no-activity"))
            return

        # Action icons
        action_icons = {
            "created": "[green]+[/]",
            "updated": "[yellow]~[/]",
            "deleted": "[red]-[/]",
            "status_changed": "[cyan]→[/]",
            "completed": "[green]✓[/]",
            "tagged": "[magenta]#[/]",
            "untagged": "[dim]#[/]",
        }

        for activity in self._activities:
            icon = action_icons.get(activity.action, "•")

            # Format time
            if activity.created_at:
                time_str = activity.created_at.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "Unknown"

            # Build description
            desc_parts = []
            if activity.entity_type:
                desc_parts.append(activity.entity_type.title())
            if activity.action:
                desc_parts.append(activity.action.replace("_", " "))

            # Show old -> new value for status changes
            value_str = ""
            if activity.old_value and activity.new_value:
                value_str = f"{activity.old_value} → {activity.new_value}"
            elif activity.new_value:
                value_str = activity.new_value

            with Vertical(classes=f"activity-item {activity.action}"):
                content.mount(
                    Static(f"{icon} {' '.join(desc_parts)}", classes="activity-header")
                )
                if value_str:
                    content.mount(Static(f"  {value_str}", classes="activity-detail"))
                if activity.notes:
                    content.mount(Static(f"  [dim]{activity.notes}[/dim]", classes="activity-detail"))
                content.mount(Static(f"  {time_str}", classes="activity-time"))

        # Pagination
        if self._total > self._page_size:
            max_page = (self._total + self._page_size - 1) // self._page_size
            with Horizontal(classes="pagination"):
                content.mount(
                    Button("← Previous", variant="default", id="prev-btn", disabled=self._page <= 1)
                )
                content.mount(
                    Static(f"Page {self._page} of {max_page}", classes="page-info")
                )
                content.mount(
                    Button("Next →", variant="default", id="next-btn", disabled=self._page >= max_page)
                )

    def action_go_dashboard(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()
