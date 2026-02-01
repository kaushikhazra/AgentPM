"""Dashboard screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from taskyn.tui.widgets.project_tree import ProjectTree
from taskyn.tui.widgets.stats_panel import StatsPanel
from taskyn.tui.widgets.task_table import TaskTable
from taskyn.tui.widgets.timer_display import TimerDisplay


class DashboardScreen(Container):
    """Main dashboard screen with project tree, task list, and panels."""

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

    def on_mount(self) -> None:
        """Initialize dashboard data."""
        pass  # Stats and timer load themselves

    def refresh_stats(self) -> None:
        """Refresh statistics panel."""
        try:
            stats = self.query_one(StatsPanel)
            stats.refresh_stats()
        except Exception:
            pass

    def get_timer(self) -> TimerDisplay | None:
        """Get the timer display widget."""
        try:
            return self.query_one(TimerDisplay)
        except Exception:
            return None
