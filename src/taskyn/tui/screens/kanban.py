"""Kanban board screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from taskyn.tui.widgets.kanban_board import KanbanBoard


class KanbanScreen(Screen):
    """Full-screen Kanban board view."""

    BINDINGS = [
        Binding("escape", "go_dashboard", "Dashboard", show=True),
        Binding("1", "go_dashboard", "Dashboard", show=False),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("ctrl+n", "new_task", "New Task", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="kanban-header"):
            yield Static("Kanban Board", id="kanban-title")

        yield KanbanBoard()
        yield Footer()

    def action_go_dashboard(self) -> None:
        """Return to dashboard."""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Refresh the board."""
        board = self.query_one(KanbanBoard)
        board.refresh_board()
        self.app.notify("Board refreshed", title="Kanban")

    def action_new_task(self) -> None:
        """Open new task dialog."""
        self.app.action_new_task()
