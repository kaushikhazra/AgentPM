"""Loading indicator widget."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static, LoadingIndicator as TextualLoadingIndicator


class LoadingOverlay(Vertical):
    """Loading overlay with spinner and message."""

    message: reactive[str] = reactive("Loading...")

    def __init__(self, message: str = "Loading...") -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(classes="loading-box"):
            yield TextualLoadingIndicator()
            yield Static(self.message, classes="loading-message", id="loading-msg")

    def watch_message(self, message: str) -> None:
        """Update the message display."""
        try:
            msg = self.query_one("#loading-msg", Static)
            msg.update(message)
        except Exception:
            pass


class LoadingMixin:
    """Mixin to add loading state to widgets."""

    _is_loading: bool = False
    _loading_overlay: LoadingOverlay | None = None

    def show_loading(self, message: str = "Loading...") -> None:
        """Show loading overlay."""
        if self._is_loading:
            return

        self._is_loading = True
        self._loading_overlay = LoadingOverlay(message)
        self.mount(self._loading_overlay)

    def hide_loading(self) -> None:
        """Hide loading overlay."""
        if not self._is_loading:
            return

        self._is_loading = False
        if self._loading_overlay:
            self._loading_overlay.remove()
            self._loading_overlay = None


class EmptyState(Vertical):
    """Empty state placeholder widget."""

    def __init__(
        self,
        icon: str = "📭",
        message: str = "Nothing here yet",
        hint: str = "",
    ) -> None:
        super().__init__()
        self._icon = icon
        self._message = message
        self._hint = hint

    def compose(self) -> ComposeResult:
        yield Static(self._icon, classes="empty-icon")
        yield Static(self._message, classes="empty-message")
        if self._hint:
            yield Static(f"[dim]{self._hint}[/dim]", classes="empty-hint")
