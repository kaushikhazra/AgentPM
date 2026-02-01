"""Main Taskyn TUI application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from taskyn.tui.commands.providers import (
    CommandsProvider,
    ProjectSearchProvider,
    TaskSearchProvider,
)


class TaskynTUI(App):
    """Taskyn Terminal User Interface."""

    TITLE = "Taskyn"
    SUB_TITLE = "AI-First Project Management"
    CSS_PATH = "taskyn.tcss"

    # Register command palette providers
    COMMANDS = App.COMMANDS | {TaskSearchProvider, ProjectSearchProvider, CommandsProvider}

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_task", "New Task", show=True),
        Binding("c", "new_company", "New Company", show=False),
        Binding("p", "new_project", "New Project", show=False),
        Binding("m", "new_milestone", "New Milestone", show=False),
        Binding("s", "new_story", "New Story", show=False),
        Binding("/", "command_palette", "Search", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=False),
        Binding("ctrl+f", "view_search", "Search", show=False),
        Binding("?", "help", "Help", show=True),
        Binding("d", "toggle_dark", "Dark/Light", show=False),
        Binding("1", "view_dashboard", "Dashboard", show=True),
        Binding("2", "view_projects", "Kanban", show=True),
        Binding("3", "view_settings", "Settings", show=True),
        Binding("4", "view_search", "Search", show=False),
        Binding("5", "view_activity", "Activity", show=False),
        Binding("6", "view_statistics", "Statistics", show=False),
    ]

    def __init__(self, dark_mode: bool = True) -> None:
        """Initialize the TUI.

        Args:
            dark_mode: Start in dark mode if True, light mode if False.
        """
        super().__init__()
        self._initial_dark_mode = dark_mode

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        # Import here to avoid circular imports
        from taskyn.tui.screens.dashboard import DashboardScreen

        yield DashboardScreen()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        if not self._initial_dark_mode:
            self.theme = "textual-light"

    def action_toggle_dark(self) -> None:
        """Toggle dark/light mode."""
        self.theme = (
            "textual-light" if self.theme == "textual-dark" else "textual-dark"
        )

    def action_new_task(self) -> None:
        """Open new task dialog."""
        from taskyn.tui.dialogs.new_task import NewTaskModal

        def on_dismiss(result: bool) -> None:
            if result:
                self._refresh_dashboard()

        self.push_screen(NewTaskModal(), on_dismiss)

    def action_new_company(self) -> None:
        """Open new company dialog."""
        from taskyn.tui.dialogs.company_form import CompanyFormModal

        def on_dismiss(result: bool) -> None:
            if result:
                self._refresh_dashboard()

        self.push_screen(CompanyFormModal(), on_dismiss)

    def action_new_project(self) -> None:
        """Open new project dialog."""
        from taskyn.tui.dialogs.project_form import ProjectFormModal

        def on_dismiss(result: bool) -> None:
            if result:
                self._refresh_dashboard()

        self.push_screen(ProjectFormModal(), on_dismiss)

    def action_new_milestone(self) -> None:
        """Open new milestone dialog."""
        from taskyn.tui.dialogs.milestone_form import MilestoneFormModal

        def on_dismiss(result: bool) -> None:
            if result:
                self._refresh_dashboard()

        self.push_screen(MilestoneFormModal(), on_dismiss)

    def action_new_story(self) -> None:
        """Open new story dialog."""
        from taskyn.tui.dialogs.story_form import StoryFormModal

        def on_dismiss(result: bool) -> None:
            if result:
                self._refresh_dashboard()

        self.push_screen(StoryFormModal(), on_dismiss)

    def action_view_search(self) -> None:
        """Switch to search screen."""
        from taskyn.tui.screens.search import SearchScreen

        if len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(SearchScreen())

    def action_view_activity(self) -> None:
        """Switch to activity screen."""
        from taskyn.tui.screens.activity import ActivityScreen

        if len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(ActivityScreen())

    def action_view_statistics(self) -> None:
        """Switch to statistics screen."""
        from taskyn.tui.screens.statistics import StatisticsScreen

        if len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(StatisticsScreen())

    def action_help(self) -> None:
        """Show help screen."""
        from taskyn.tui.screens.help import HelpScreen

        self.push_screen(HelpScreen())

    def action_view_dashboard(self) -> None:
        """Switch to dashboard view."""
        # Pop all screens to get back to dashboard
        while len(self.screen_stack) > 1:
            self.pop_screen()

    def action_view_projects(self) -> None:
        """Switch to Kanban board view."""
        from taskyn.tui.screens.kanban import KanbanScreen

        # If already on a screen, pop first
        if len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(KanbanScreen())

    def action_view_settings(self) -> None:
        """Switch to settings view."""
        from taskyn.tui.screens.settings import SettingsScreen

        # If already on a screen, pop first
        if len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(SettingsScreen())

    def on_task_table_task_selected(self, event) -> None:
        """Handle task selection from table."""
        from taskyn.tui.screens.task_detail import TaskDetailScreen

        self.push_screen(TaskDetailScreen(event.task_id))

    def on_project_tree_node_selected(self, event) -> None:
        """Handle node selection from project tree."""
        if event.node_type in ("task", "story"):
            from taskyn.tui.screens.task_detail import TaskDetailScreen

            self.push_screen(TaskDetailScreen(event.node_id))
        elif event.node_type == "company":
            from taskyn.tui.screens.company_detail import CompanyDetailScreen

            self.push_screen(CompanyDetailScreen(event.node_id))
        elif event.node_type == "project":
            from taskyn.tui.screens.project_detail import ProjectDetailScreen

            self.push_screen(ProjectDetailScreen(event.node_id))
        elif event.node_type == "milestone":
            from taskyn.tui.screens.milestone_detail import MilestoneDetailScreen

            self.push_screen(MilestoneDetailScreen(event.node_id))
        else:
            # Unknown type - just notify
            self.notify(f"Selected: {event.node_name}", title=event.node_type.title())

    def _refresh_dashboard(self) -> None:
        """Refresh dashboard widgets after data changes."""
        try:
            from taskyn.tui.screens.dashboard import DashboardScreen
            from taskyn.tui.widgets.project_tree import ProjectTree
            from taskyn.tui.widgets.task_table import TaskTable

            # Refresh task table
            task_table = self.query_one(TaskTable)
            task_table.refresh_tasks()

            # Refresh project tree
            project_tree = self.query_one(ProjectTree)
            project_tree.refresh_tree()

            # Refresh stats and activity
            dashboard = self.query_one(DashboardScreen)
            dashboard.refresh_stats()
            dashboard.refresh_activity()

        except Exception:
            pass  # Widgets might not exist yet

    def open_edit_task(self, task_id: str) -> None:
        """Open edit dialog for a task."""
        from taskyn.tui.dialogs.edit_task import EditTaskModal

        def on_dismiss(result: bool) -> None:
            if result:
                self._refresh_dashboard()

        self.push_screen(EditTaskModal(task_id), on_dismiss)

    def open_status_picker(self, task_id: str, current_status: str) -> None:
        """Open status picker for a task."""
        from taskyn.tui.dialogs.status_picker import StatusPickerDialog

        def on_dismiss(new_status: str | None) -> None:
            if new_status:
                self._change_task_status(task_id, new_status)

        self.push_screen(StatusPickerDialog(task_id, current_status), on_dismiss)

    def _change_task_status(self, task_id: str, new_status: str) -> None:
        """Change task status."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.workflow import transition_status

            with get_db() as db:
                transition_status(db, task_id, new_status)

            self.notify(f"Status changed to {new_status}", title="Updated")
            self._refresh_dashboard()

        except Exception as e:
            self.notify(f"Error: {e}", title="Failed", severity="error")

    def confirm_delete_task(self, task_id: str, task_title: str) -> None:
        """Show delete confirmation for a task."""
        from taskyn.tui.dialogs.confirm import ConfirmDialog

        def on_dismiss(confirmed: bool) -> None:
            if confirmed:
                self._delete_task(task_id, task_title)

        self.push_screen(
            ConfirmDialog(
                message=f'Delete "{task_title}"?\n\nThis action cannot be undone.',
                title="Delete Task",
                confirm_label="Delete",
                cancel_label="Cancel",
                destructive=True,
            ),
            on_dismiss,
        )

    def _delete_task(self, task_id: str, task_title: str) -> None:
        """Delete a task."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import delete_node

            with get_db() as db:
                delete_node(db, task_id)

            self.notify(f"Deleted: {task_title}", title="Deleted")
            self._refresh_dashboard()

            # Pop back to dashboard if viewing deleted task
            if len(self.screen_stack) > 1:
                self.pop_screen()

        except Exception as e:
            self.notify(f"Error: {e}", title="Failed", severity="error")

    def toggle_timer(self, task_id: str, task_title: str) -> None:
        """Toggle timer for a task."""
        try:
            from taskyn.tui.screens.dashboard import DashboardScreen
            from taskyn.tui.widgets.timer_display import TimerDisplay

            # Get timer display from dashboard
            dashboard = self.query_one(DashboardScreen)
            timer = dashboard.get_timer()

            if timer is None:
                self.notify("Timer not available", title="Error", severity="error")
                return

            # Check if this task's timer is already running
            if timer.is_running and timer.task_id == task_id:
                # Stop the timer
                timer.stop_timer()
                self.notify(f"Timer stopped for: {task_title}", title="Timer Stopped")
            else:
                # Start timer for this task (will stop any existing timer)
                timer.start_timer(task_id, task_title)
                self.notify(f"Timer started for: {task_title}", title="Timer Started")

        except Exception as e:
            self.notify(f"Error: {e}", title="Timer Error", severity="error")

    def on_timer_display_timer_started(self, event) -> None:
        """Handle timer started event."""
        self._refresh_dashboard()

    def on_timer_display_timer_stopped(self, event) -> None:
        """Handle timer stopped event."""
        # Format elapsed time
        seconds = event.elapsed_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = f"{minutes}m"

        self.notify(f"Logged {time_str}", title="Time Saved")
        self._refresh_dashboard()


def main() -> None:
    """Run the TUI."""
    app = TaskynTUI()
    app.run()


if __name__ == "__main__":
    main()
