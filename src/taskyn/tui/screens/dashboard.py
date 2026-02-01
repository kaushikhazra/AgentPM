"""Dashboard screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from taskyn.tui.widgets.project_tree import ProjectTree
from taskyn.tui.widgets.task_table import TaskTable


class StatsPanel(Static):
    """Statistics panel showing progress."""

    def compose(self) -> ComposeResult:
        yield Static("Progress", classes="panel-title")
        yield Static("Sprint Progress: 0/0 (0%)", id="progress-label")
        yield Static("[dim]No tasks yet[/dim]", id="progress-bar")


class TimerPanel(Static):
    """Timer panel showing active timer."""

    def compose(self) -> ComposeResult:
        yield Static("Timer", classes="panel-title")
        yield Static("00:00:00", id="timer-display", classes="timer-display")
        yield Static("No active timer", id="timer-task", classes="timer-task")


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
            yield TimerPanel(id="timer-panel")

    def on_mount(self) -> None:
        """Initialize dashboard data."""
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Refresh statistics panel."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                nodes = list_nodes(db)
                tasks = [n for n in nodes if n.node_type in ("task", "story")]
                done = [t for t in tasks if t.status == "done"]

                total = len(tasks)
                completed = len(done)
                percent = (completed / total * 100) if total > 0 else 0

                progress_label = self.query_one("#progress-label", Static)
                progress_label.update(f"Tasks: {completed}/{total} ({percent:.0f}%)")

                # Simple text-based progress bar
                bar_width = 20
                filled = int(bar_width * (percent / 100))
                bar = "█" * filled + "░" * (bar_width - filled)
                progress_bar = self.query_one("#progress-bar", Static)
                progress_bar.update(f"[#8B5CF6]{bar}[/]")

        except Exception:
            # Database might not exist yet
            pass
