"""Help screen showing keyboard shortcuts."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static


HELP_TEXT = """\
[bold]Taskyn Keyboard Shortcuts[/]

[bold]Global[/]
  q           Quit Taskyn
  /           Open command palette (search)
  Ctrl+P      Open command palette
  ?           Show this help
  d           Toggle dark/light mode

[bold]Create[/]
  Ctrl+N      Create new task
  c           Create new company
  p           Create new project
  m           Create new milestone
  s           Create new story

[bold]Views[/]
  1           Go to Dashboard
  2           Go to Kanban
  3           Go to Settings
  4           Go to Search
  5           Go to Activity
  6           Go to Statistics

[bold]Navigation[/]
  ↑ / k       Move up
  ↓ / j       Move down
  ← / h       Collapse / Go left
  → / l       Expand / Go right
  Enter       Select / Open
  Escape      Back / Cancel
  Tab         Next element
  Shift+Tab   Previous element

[bold]Task Detail View[/]
  e           Edit task
  s           Change status
  t           Toggle timer
  d           Delete task
  Escape      Back to dashboard

[bold]Timer[/]
  t           Start/Stop timer (in task view)
  Space       Pause/Resume (in timer panel)

[bold]Command Palette[/]
  ↑ / ↓       Navigate results
  Enter       Select result
  Escape      Close palette

[dim]Press Escape or ? to close this help[/]
"""


class HelpScreen(ModalScreen):
    """Modal screen showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("?", "close", "Close", show=False),
        Binding("q", "close", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal-dialog-wide"):
            yield Static(HELP_TEXT, id="help-content")

    def action_close(self) -> None:
        """Close the help screen."""
        self.dismiss()
