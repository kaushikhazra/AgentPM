"""Dashboard screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from taskyn.tui.widgets.activity_log import ActivityLog
from taskyn.tui.widgets.project_tree import ProjectTree
from taskyn.tui.widgets.stats_panel import StatsPanel
from taskyn.tui.widgets.task_table import TaskTable
from taskyn.tui.widgets.timer_display import TimerDisplay


class DashboardScreen(Container):
    """Main dashboard screen with project tree, task list, and panels."""

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Static("Projects", classes="panel-title")
            yield ProjectTree()

        with Vertical(id="main-content"):
            yield Static("Tasks", classes="panel-title")
            yield TaskTable()

        with Horizontal(id="bottom-panels"):
            yield StatsPanel(id="stats-panel")
            with Vertical(id="timer-panel"):
                yield Static("Timer", classes="panel-title")
                yield TimerDisplay(compact=True)

        yield ActivityLog(id="activity-panel")

    def on_mount(self) -> None:
        """Initialize dashboard data."""
        self._update_layout()

    def on_resize(self, event) -> None:
        """Handle terminal resize."""
        self._update_layout()

    def _update_layout(self) -> None:
        """Update layout based on terminal size."""
        width = self.app.size.width

        self.remove_class("-narrow", "-compact")

        if width < 100:
            self.add_class("-narrow")
        elif width < 120:
            self.add_class("-compact")

    def refresh_stats(self) -> None:
        """Refresh statistics panel."""
        try:
            stats = self.query_one(StatsPanel)
            stats.refresh_stats()
        except Exception:
            pass

    def refresh_activity(self) -> None:
        """Refresh activity log."""
        try:
            activity = self.query_one(ActivityLog)
            activity.refresh_activities()
        except Exception:
            pass

    def get_timer(self) -> TimerDisplay | None:
        """Get the timer display widget."""
        try:
            return self.query_one(TimerDisplay)
        except Exception:
            return None
