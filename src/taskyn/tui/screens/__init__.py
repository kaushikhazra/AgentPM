"""TUI screens."""

from taskyn.tui.screens.dashboard import DashboardScreen
from taskyn.tui.screens.help import HelpScreen
from taskyn.tui.screens.kanban import KanbanScreen
from taskyn.tui.screens.settings import SettingsScreen
from taskyn.tui.screens.task_detail import TaskDetailScreen

__all__ = [
    "DashboardScreen",
    "HelpScreen",
    "KanbanScreen",
    "SettingsScreen",
    "TaskDetailScreen",
]
