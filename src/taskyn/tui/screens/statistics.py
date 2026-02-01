"""Statistics screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Select, Static


class StatisticsScreen(Screen):
    """Full project statistics screen."""

    DEFAULT_CSS = """
    StatisticsScreen {
        background: $surface;
    }

    #stats-header {
        height: auto;
        padding: 1 2;
        background: $surface-darken-1;
    }

    #stats-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    #project-row {
        height: auto;
    }

    .filter-label {
        width: auto;
        padding: 1 1 0 0;
    }

    #project-select {
        width: 40;
    }

    #stats-content {
        padding: 1 2;
    }

    .stats-section {
        margin-bottom: 2;
        padding: 1 2;
        border: solid $surface-lighten-1;
        background: $surface-darken-1;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    .stat-row {
        height: auto;
        padding: 0 1;
    }

    .stat-label {
        width: 20;
    }

    .stat-value {
        width: 1fr;
    }

    .progress-bar {
        padding: 1 0;
    }

    .milestone-row {
        padding: 0 1;
    }

    .blocker-item {
        padding: 0 1;
        color: $error;
    }

    .no-data {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("1", "go_dashboard", "Dashboard", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._projects = []
        self._selected_project_id = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="stats-header"):
            yield Static("Project Statistics", id="stats-title")

            with Horizontal(id="project-row"):
                yield Label("Project:", classes="filter-label")
                yield Select(
                    options=[("All Projects", "")],
                    value="",
                    id="project-select",
                )

        yield VerticalScroll(id="stats-content")
        yield Footer()

    def on_mount(self) -> None:
        """Load projects and stats on mount."""
        self._load_projects()
        self._load_stats()

    def _load_projects(self) -> None:
        """Load project options."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.project import list_projects

            with get_db() as db:
                self._projects = list_projects(db)

            options = [("All Projects", "")]
            for project in sorted(self._projects, key=lambda p: p.name):
                options.append((project.name, project.id))

            select = self.query_one("#project-select", Select)
            select.set_options(options)

        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        """Reload stats when project changes."""
        self._selected_project_id = event.value if event.value else None
        self._load_stats()

    def action_refresh(self) -> None:
        """Refresh statistics."""
        self._load_stats()

    def _load_stats(self) -> None:
        """Load and display statistics."""
        content = self.query_one("#stats-content", VerticalScroll)
        content.remove_children()

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.reporting import get_project_stats, get_dashboard
            from taskyn.core.milestone import list_milestones
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                if self._selected_project_id:
                    # Single project stats
                    stats = get_project_stats(db, self._selected_project_id)
                    self._render_project_stats(content, stats)
                else:
                    # Overall stats
                    dashboard = get_dashboard(db)
                    all_nodes = list_nodes(db)
                    all_milestones = list_milestones(db)
                    self._render_overall_stats(content, dashboard, all_nodes, all_milestones)

        except Exception as e:
            content.mount(Static(f"[red]Error loading stats: {e}[/red]", classes="no-data"))

    def _render_overall_stats(self, content, dashboard, all_nodes, all_milestones) -> None:
        """Render overall statistics."""
        # Summary section
        with Vertical(classes="stats-section"):
            content.mount(Static("Overview", classes="section-title"))

            total_tasks = len([n for n in all_nodes if n.node_type in ("task", "story")])
            done_tasks = len([n for n in all_nodes if n.node_type in ("task", "story") and n.status == "done"])
            in_progress = len([n for n in all_nodes if n.status == "in_progress"])

            with Horizontal(classes="stat-row"):
                content.mount(Static("Total Items:", classes="stat-label"))
                content.mount(Static(str(total_tasks), classes="stat-value"))

            with Horizontal(classes="stat-row"):
                content.mount(Static("Completed:", classes="stat-label"))
                content.mount(Static(str(done_tasks), classes="stat-value"))

            with Horizontal(classes="stat-row"):
                content.mount(Static("In Progress:", classes="stat-label"))
                content.mount(Static(str(in_progress), classes="stat-value"))

            if total_tasks > 0:
                percent = int((done_tasks / total_tasks) * 100)
                bar_width = 30
                filled = int(bar_width * done_tasks / total_tasks)
                empty = bar_width - filled

                bar = "[green]" + "█" * filled + "[/][dim]" + "░" * empty + "[/]"
                content.mount(Static(f"\n  {bar} {percent}% complete", classes="progress-bar"))

        # Time tracking section
        with Vertical(classes="stats-section"):
            content.mount(Static("Time Tracking", classes="section-title"))

            today_minutes = dashboard.today_time_minutes if hasattr(dashboard, 'today_time_minutes') else 0
            today_hours = today_minutes // 60
            today_mins = today_minutes % 60

            with Horizontal(classes="stat-row"):
                content.mount(Static("Today:", classes="stat-label"))
                content.mount(Static(f"{today_hours}h {today_mins}m", classes="stat-value"))

        # Blockers section
        blocked_nodes = [n for n in all_nodes if n.status == "blocked"]
        if blocked_nodes:
            with Vertical(classes="stats-section"):
                content.mount(Static(f"Blockers ({len(blocked_nodes)})", classes="section-title"))

                for node in blocked_nodes[:10]:
                    reason = node.blocked_reason or "No reason specified"
                    content.mount(
                        Static(f"  ✗ {node.title}: {reason}", classes="blocker-item")
                    )

        # Milestones section
        open_milestones = [m for m in all_milestones if m.status != "completed"]
        if open_milestones:
            with Vertical(classes="stats-section"):
                content.mount(Static(f"Open Milestones ({len(open_milestones)})", classes="section-title"))

                for ms in sorted(open_milestones, key=lambda m: m.target_date or "9999"):
                    date_str = ms.target_date.strftime("%Y-%m-%d") if ms.target_date else "No date"
                    content.mount(
                        Static(f"  🎯 {ms.name} ({date_str})", classes="milestone-row")
                    )

    def _render_project_stats(self, content, stats) -> None:
        """Render single project statistics."""
        # Summary section
        with Vertical(classes="stats-section"):
            content.mount(Static("Project Summary", classes="section-title"))

            with Horizontal(classes="stat-row"):
                content.mount(Static("Total Items:", classes="stat-label"))
                content.mount(Static(str(stats.total_nodes), classes="stat-value"))

        # Status breakdown
        with Vertical(classes="stats-section"):
            content.mount(Static("By Status", classes="section-title"))

            for status, count in stats.nodes_by_status.items():
                with Horizontal(classes="stat-row"):
                    content.mount(Static(f"{status.replace('_', ' ').title()}:", classes="stat-label"))
                    content.mount(Static(str(count), classes="stat-value"))

        # Time tracking
        with Vertical(classes="stats-section"):
            content.mount(Static("Time Tracked", classes="section-title"))

            def format_time(minutes):
                hours = minutes // 60
                mins = minutes % 60
                return f"{hours}h {mins}m"

            with Horizontal(classes="stat-row"):
                content.mount(Static("This Week:", classes="stat-label"))
                content.mount(Static(format_time(stats.time_this_week), classes="stat-value"))

            with Horizontal(classes="stat-row"):
                content.mount(Static("This Month:", classes="stat-label"))
                content.mount(Static(format_time(stats.time_this_month), classes="stat-value"))

            with Horizontal(classes="stat-row"):
                content.mount(Static("Total:", classes="stat-label"))
                content.mount(Static(format_time(stats.time_total), classes="stat-value"))

        # Velocity
        if stats.velocity_per_week:
            with Vertical(classes="stats-section"):
                content.mount(Static("Velocity (items/week)", classes="section-title"))
                content.mount(
                    Static(f"  Average: {stats.velocity_per_week:.1f} items/week", classes="stat-row")
                )

        # Milestone progress
        if stats.milestone_progress:
            with Vertical(classes="stats-section"):
                content.mount(Static("Milestone Progress", classes="section-title"))

                for mp in stats.milestone_progress:
                    ms = mp.milestone
                    total = mp.total_items
                    done = mp.completed_items

                    if total > 0:
                        percent = int((done / total) * 100)
                        bar_width = 20
                        filled = int(bar_width * done / total)
                        empty = bar_width - filled

                        bar = "[green]" + "█" * filled + "[/][dim]" + "░" * empty + "[/]"
                        content.mount(
                            Static(f"  {ms.name}: {bar} {percent}%", classes="milestone-row")
                        )
                    else:
                        content.mount(
                            Static(f"  {ms.name}: [dim]No items[/dim]", classes="milestone-row")
                        )

        # Blockers
        if stats.blockers:
            with Vertical(classes="stats-section"):
                content.mount(Static(f"Blockers ({len(stats.blockers)})", classes="section-title"))

                for blocker in stats.blockers[:10]:
                    reason = blocker.blocked_reason or "No reason"
                    content.mount(
                        Static(f"  ✗ {blocker.title}: {reason}", classes="blocker-item")
                    )

    def action_go_dashboard(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()
