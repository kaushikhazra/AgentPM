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

    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 2 3;
        grid-columns: 1fr 3fr;
        grid-rows: 1fr auto auto;
        grid-gutter: 1;
    }

    DashboardScreen #sidebar {
        row-span: 3;
        border: solid #8B5CF6;
        background: $surface-darken-1;
        padding: 1;
    }

    DashboardScreen #main-content {
        border: solid #64748B;
        background: $surface-darken-1;
    }

    DashboardScreen #bottom-panels {
        layout: horizontal;
    }

    DashboardScreen #stats-panel {
        width: 1fr;
        border: solid #64748B;
        background: $surface-darken-1;
        padding: 1;
    }

    DashboardScreen #timer-panel {
        width: 1fr;
        border: solid #06B6D4;
        background: $surface-darken-1;
        padding: 1;
    }

    DashboardScreen #activity-panel {
        column-span: 1;
        border: solid #64748B;
        background: $surface-darken-1;
        padding: 1;
        max-height: 10;
    }

    /* Narrow layout - hide sidebar */
    DashboardScreen.-narrow {
        grid-size: 1 3;
        grid-columns: 1fr;
    }

    DashboardScreen.-narrow #sidebar {
        display: none;
    }

    /* Compact layout - smaller sidebar */
    DashboardScreen.-compact #sidebar {
        width: 22;
    }
    """

    def compose(self) -> ComposeResult:
        # Sidebar with project tree
        with Vertical(id="sidebar"):
            yield Static("Projects", classes="panel-title")
            yield ProjectTree()

        # Main content with task table
        with Vertical(id="main-content"):
            yield Static("Tasks", classes="panel-title")
            yield TaskTable()

        # Bottom panels
        with Horizontal(id="bottom-panels"):
            yield StatsPanel(id="stats-panel")
            with Vertical(id="timer-panel"):
                yield Static("Timer", classes="panel-title")
                yield TimerDisplay(compact=True)

        # Activity log
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

        # Remove existing layout classes
        self.remove_class("-narrow", "-compact")

        # Apply appropriate layout class
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
