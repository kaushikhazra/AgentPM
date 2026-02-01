"""Progress chart widget for ASCII visualization."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class ProgressChart(Vertical):
    """ASCII progress bar chart widget."""

    def __init__(
        self,
        data: dict[str, int] | None = None,
        title: str = "",
        bar_width: int = 30,
        show_percentage: bool = True,
        colors: dict[str, str] | None = None,
    ) -> None:
        """Initialize the progress chart.

        Args:
            data: Dictionary of label -> value
            title: Chart title
            bar_width: Width of progress bars in characters
            show_percentage: Whether to show percentage labels
            colors: Dictionary of label -> color
        """
        super().__init__()
        self.data = data or {}
        self.chart_title = title
        self.bar_width = bar_width
        self.show_percentage = show_percentage
        self.colors = colors or {}

    def compose(self) -> ComposeResult:
        if self.chart_title:
            yield Static(self.chart_title, classes="chart-title")

        if not self.data:
            yield Static("[dim]No data[/dim]")
            return

        # Calculate total and max for scaling
        total = sum(self.data.values())
        max_value = max(self.data.values()) if self.data else 1

        for label, value in self.data.items():
            # Calculate bar fill
            if total > 0:
                percent = (value / total) * 100
                fill_ratio = value / max_value
            else:
                percent = 0
                fill_ratio = 0

            filled = int(self.bar_width * fill_ratio)
            empty = self.bar_width - filled

            # Get color for this label
            color = self.colors.get(label, "green")

            # Build bar
            bar = f"[{color}]" + "█" * filled + "[/][dim]" + "░" * empty + "[/]"

            # Build label
            if self.show_percentage:
                label_str = f"{label}: {bar} {value} ({percent:.0f}%)"
            else:
                label_str = f"{label}: {bar} {value}"

            yield Static(label_str, classes="chart-row")

    def update_data(self, data: dict[str, int]) -> None:
        """Update chart data and refresh."""
        self.data = data
        self.refresh()


class StatusChart(ProgressChart):
    """Progress chart with status-specific colors."""

    STATUS_COLORS = {
        "backlog": "dim",
        "ready": "blue",
        "in_progress": "yellow",
        "done": "green",
        "blocked": "red",
        "todo": "cyan",
    }

    def __init__(
        self,
        data: dict[str, int] | None = None,
        title: str = "By Status",
        bar_width: int = 25,
    ) -> None:
        super().__init__(
            data=data,
            title=title,
            bar_width=bar_width,
            show_percentage=True,
            colors=self.STATUS_COLORS,
        )


class MilestoneProgressChart(Vertical):
    """Chart showing progress across multiple milestones."""

    def __init__(
        self,
        milestones: list | None = None,
        title: str = "Milestone Progress",
        bar_width: int = 20,
    ) -> None:
        """Initialize milestone progress chart.

        Args:
            milestones: List of milestone progress data
            title: Chart title
            bar_width: Width of progress bars
        """
        super().__init__()
        self.milestones = milestones or []
        self.chart_title = title
        self.bar_width = bar_width

    def compose(self) -> ComposeResult:
        if self.chart_title:
            yield Static(self.chart_title, classes="chart-title")

        if not self.milestones:
            yield Static("[dim]No milestones[/dim]")
            return

        from datetime import date

        for mp in self.milestones:
            ms = mp.milestone if hasattr(mp, 'milestone') else mp
            total = mp.total_items if hasattr(mp, 'total_items') else 0
            done = mp.completed_items if hasattr(mp, 'completed_items') else 0

            # Calculate progress
            if total > 0:
                percent = int((done / total) * 100)
                filled = int(self.bar_width * done / total)
            else:
                percent = 0
                filled = 0
            empty = self.bar_width - filled

            bar = "[green]" + "█" * filled + "[/][dim]" + "░" * empty + "[/]"

            # Check if overdue
            is_overdue = False
            date_str = ""
            if hasattr(ms, 'target_date') and ms.target_date:
                date_str = f" ({ms.target_date.strftime('%Y-%m-%d')})"
                if ms.status != "completed" and ms.target_date < date.today():
                    is_overdue = True

            name = ms.name if hasattr(ms, 'name') else str(ms)
            if is_overdue:
                yield Static(
                    f"[red]🎯 {name}{date_str}[/]\n  {bar} {percent}%",
                    classes="milestone-row overdue"
                )
            else:
                yield Static(
                    f"🎯 {name}{date_str}\n  {bar} {percent}%",
                    classes="milestone-row"
                )

    def update_milestones(self, milestones: list) -> None:
        """Update milestone data and refresh."""
        self.milestones = milestones
        self.refresh()
