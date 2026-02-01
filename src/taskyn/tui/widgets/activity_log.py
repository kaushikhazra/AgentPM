"""Activity log widget showing recent actions."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static


class ActivityLog(Vertical):
    """Widget displaying recent activity."""

    def __init__(self, max_items: int = 10, id: str | None = None) -> None:
        super().__init__(id=id)
        self._max_items = max_items
        self._activities: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Static("Activity", classes="activity-title")
        yield VerticalScroll(id="activity-list")

    def on_mount(self) -> None:
        """Load recent activities."""
        self.refresh_activities()

    def refresh_activities(self) -> None:
        """Load activities from database."""
        activity_list = self.query_one("#activity-list", VerticalScroll)
        activity_list.remove_children()

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.activity import get_recent_activity

            with get_db() as db:
                activities = get_recent_activity(db, limit=self._max_items)

                if not activities:
                    activity_list.mount(
                        Static("[dim]No recent activity[/dim]", classes="activity-empty")
                    )
                    return

                for activity in activities:
                    self._add_activity_item(activity_list, activity)

        except Exception:
            # Show empty state if database doesn't exist
            activity_list.mount(
                Static("[dim]No recent activity[/dim]", classes="activity-empty")
            )

    def _add_activity_item(self, container, activity) -> None:
        """Add an activity item to the list."""
        # Format timestamp
        if activity.created_at:
            time_str = activity.created_at.strftime("%H:%M")
        else:
            time_str = "??:??"

        # Format action with color
        action = activity.action or "action"
        action_colors = {
            "created": "#10B981",  # Emerald
            "updated": "#F59E0B",  # Amber
            "deleted": "#F43F5E",  # Rose
            "status_changed": "#8B5CF6",  # Purple
            "timer_started": "#06B6D4",  # Cyan
            "timer_stopped": "#06B6D4",  # Cyan
        }
        color = action_colors.get(action, "#94A3B8")

        # Build display text
        entity = activity.entity_type or "item"
        title = activity.entity_title or "Unknown"

        # Truncate title if needed
        if len(title) > 30:
            title = title[:27] + "..."

        action_display = action.replace("_", " ").title()

        text = f"[#64748B]{time_str}[/]  [{color}]{action_display}[/] {entity}: {title}"

        container.mount(Static(text, classes="activity-item"))

    def log_activity(
        self,
        action: str,
        entity_type: str,
        entity_title: str,
    ) -> None:
        """Add a new activity entry (for real-time updates)."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.activity import log_activity as db_log_activity

            with get_db() as db:
                db_log_activity(
                    db,
                    action=action,
                    entity_type=entity_type,
                    entity_title=entity_title,
                )

            # Refresh the display
            self.refresh_activities()

        except Exception:
            pass
