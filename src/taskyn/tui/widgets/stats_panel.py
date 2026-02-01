"""Statistics panel widget."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class StatsPanel(Vertical):
    """Panel showing task statistics and progress."""

    DEFAULT_CSS = """
    StatsPanel {
        height: auto;
        padding: 1;
    }

    StatsPanel .stats-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    StatsPanel .stats-row {
        height: auto;
        padding: 0 0 1 0;
    }

    StatsPanel .progress-bar-container {
        height: 1;
        padding: 1 0;
    }

    StatsPanel .priority-stats {
        height: auto;
    }

    StatsPanel .high-priority {
        color: #F43F5E;
    }

    StatsPanel .med-priority {
        color: #F59E0B;
    }

    StatsPanel .low-priority {
        color: #94A3B8;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Progress", classes="stats-title")
        yield Static("Tasks: 0/0 (0%)", id="stats-progress", classes="stats-row")
        yield Static("", id="stats-bar", classes="progress-bar-container")
        yield Static("", id="stats-priorities", classes="priority-stats")
        yield Static("", id="stats-today", classes="stats-row")

    def on_mount(self) -> None:
        """Load stats on mount."""
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Refresh statistics from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                nodes = list_nodes(db)
                tasks = [n for n in nodes if n.node_type in ("task", "story")]

                # Count by status
                done = [t for t in tasks if t.status == "done"]
                in_progress = [t for t in tasks if t.status == "in_progress"]
                todo = [t for t in tasks if t.status in ("todo", "ready")]
                backlog = [t for t in tasks if t.status == "backlog"]

                total = len(tasks)
                completed = len(done)
                percent = (completed / total * 100) if total > 0 else 0

                # Update progress text
                progress = self.query_one("#stats-progress", Static)
                progress.update(f"Tasks: {completed}/{total} ({percent:.0f}%)")

                # Update progress bar
                bar_width = 20
                filled = int(bar_width * (percent / 100))
                bar = "█" * filled + "░" * (bar_width - filled)
                bar_widget = self.query_one("#stats-bar", Static)
                bar_widget.update(f"[#8B5CF6]{bar}[/]")

                # Count by priority
                high = sum(1 for t in tasks if (t.metadata or {}).get("priority") == "high" and t.status != "done")
                med = sum(1 for t in tasks if (t.metadata or {}).get("priority") == "medium" and t.status != "done")
                low = sum(1 for t in tasks if (t.metadata or {}).get("priority") == "low" and t.status != "done")

                priorities = self.query_one("#stats-priorities", Static)
                priorities.update(
                    f"[#F43F5E]▲ {high} High[/]  "
                    f"[#F59E0B]─ {med} Med[/]  "
                    f"[#94A3B8]▼ {low} Low[/]"
                )

                # Today's stats
                today_widget = self.query_one("#stats-today", Static)
                today_widget.update(
                    f"[#10B981]✓ {completed} done[/]  "
                    f"[#F59E0B]◐ {len(in_progress)} active[/]  "
                    f"[#8B5CF6]● {len(todo)} todo[/]"
                )

        except Exception:
            # Database might not exist yet
            pass
