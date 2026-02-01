"""Help screen showing keyboard shortcuts."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static


HELP_TEXT = """\
[bold #8B5CF6]Taskyn Keyboard Shortcuts[/]

[bold #06B6D4]Global[/]
  [#F59E0B]q[/]           Quit Taskyn
  [#F59E0B]Ctrl+N[/]      Create new task
  [#F59E0B]/[/]           Open command palette (search)
  [#F59E0B]Ctrl+P[/]      Open command palette
  [#F59E0B]?[/]           Show this help
  [#F59E0B]d[/]           Toggle dark/light mode
  [#F59E0B]1[/]           Go to Dashboard
  [#F59E0B]2[/]           Go to Projects
  [#F59E0B]3[/]           Go to Settings

[bold #06B6D4]Navigation[/]
  [#F59E0B]↑ / k[/]       Move up
  [#F59E0B]↓ / j[/]       Move down
  [#F59E0B]← / h[/]       Collapse / Go left
  [#F59E0B]→ / l[/]       Expand / Go right
  [#F59E0B]Enter[/]       Select / Open
  [#F59E0B]Escape[/]      Back / Cancel
  [#F59E0B]Tab[/]         Next element
  [#F59E0B]Shift+Tab[/]   Previous element

[bold #06B6D4]Task Detail View[/]
  [#F59E0B]e[/]           Edit task
  [#F59E0B]s[/]           Change status
  [#F59E0B]t[/]           Toggle timer
  [#F59E0B]d[/]           Delete task
  [#F59E0B]Escape[/]      Back to dashboard

[bold #06B6D4]Timer[/]
  [#F59E0B]t[/]           Start/Stop timer (in task view)
  [#F59E0B]Space[/]       Pause/Resume (in timer panel)

[bold #06B6D4]Command Palette[/]
  [#F59E0B]↑ / ↓[/]       Navigate results
  [#F59E0B]Enter[/]       Select result
  [#F59E0B]Escape[/]      Close palette

[dim]Press [#F59E0B]Escape[/] or [#F59E0B]?[/] to close this help[/]
"""


class HelpScreen(ModalScreen):
    """Modal screen showing keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-container {
        width: 60;
        height: 80%;
        max-height: 40;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #help-content {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("?", "close", "Close", show=False),
        Binding("q", "close", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-container"):
            yield Static(HELP_TEXT, id="help-content")

    def action_close(self) -> None:
        """Close the help screen."""
        self.dismiss()
