"""Main Taskyn TUI application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header


class TaskynTUI(App):
    """Taskyn Terminal User Interface."""

    TITLE = "Taskyn"
    SUB_TITLE = "AI-First Project Management"
    CSS_PATH = "taskyn.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+n", "new_task", "New Task", show=True),
        Binding("/", "search", "Search", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("d", "toggle_dark", "Dark/Light", show=False),
        Binding("1", "view_dashboard", "Dashboard", show=False),
        Binding("2", "view_projects", "Projects", show=False),
        Binding("3", "view_settings", "Settings", show=False),
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
        self.notify("New task dialog coming soon!", title="TODO")

    def action_search(self) -> None:
        """Open search/command palette."""
        self.notify("Search coming soon!", title="TODO")

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "Keyboard shortcuts:\n"
            "q - Quit\n"
            "Ctrl+N - New Task\n"
            "/ - Search\n"
            "d - Toggle Dark Mode",
            title="Help",
        )

    def action_view_dashboard(self) -> None:
        """Switch to dashboard view."""
        pass  # Already on dashboard

    def action_view_projects(self) -> None:
        """Switch to projects view."""
        self.notify("Projects view coming soon!", title="TODO")

    def action_view_settings(self) -> None:
        """Switch to settings view."""
        self.notify("Settings coming soon!", title="TODO")

    def on_task_table_task_selected(self, event) -> None:
        """Handle task selection from table."""
        from taskyn.tui.screens.task_detail import TaskDetailScreen

        self.push_screen(TaskDetailScreen(event.task_id))

    def on_project_tree_node_selected(self, event) -> None:
        """Handle node selection from project tree."""
        if event.node_type in ("task", "story"):
            from taskyn.tui.screens.task_detail import TaskDetailScreen

            self.push_screen(TaskDetailScreen(event.node_id))
        else:
            # Filter task table by selected project/milestone
            self.notify(f"Selected: {event.node_name}", title=event.node_type.title())


def main() -> None:
    """Run the TUI."""
    app = TaskynTUI()
    app.run()


if __name__ == "__main__":
    main()
