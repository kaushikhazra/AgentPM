"""Timer display widget for time tracking."""

from datetime import datetime, timedelta
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Digits, Static


class TimerDisplay(Vertical):
    """Widget displaying active timer with controls."""

    DEFAULT_CSS = """
    TimerDisplay {
        height: auto;
        padding: 1;
    }

    TimerDisplay #timer-digits {
        text-align: center;
        width: 100%;
        color: $accent;
    }

    TimerDisplay #timer-task-name {
        text-align: center;
        color: $text-muted;
        padding: 1 0;
    }

    TimerDisplay #timer-controls {
        align: center middle;
        height: auto;
        padding-top: 1;
    }

    TimerDisplay #timer-controls Button {
        margin: 0 1;
        min-width: 10;
    }

    TimerDisplay .recording-indicator {
        text-align: center;
        color: $error;
        text-style: bold;
    }

    TimerDisplay .paused-indicator {
        text-align: center;
        color: $warning;
    }

    TimerDisplay .idle-indicator {
        text-align: center;
        color: $text-muted;
    }
    """

    # Reactive state
    elapsed_seconds: reactive[int] = reactive(0)
    is_running: reactive[bool] = reactive(False)
    is_paused: reactive[bool] = reactive(False)
    task_id: reactive[str | None] = reactive(None)
    task_name: reactive[str] = reactive("No active timer")

    class TimerStarted(Message):
        """Posted when timer is started."""

        def __init__(self, task_id: str) -> None:
            super().__init__()
            self.task_id = task_id

    class TimerStopped(Message):
        """Posted when timer is stopped."""

        def __init__(self, task_id: str, elapsed_seconds: int) -> None:
            super().__init__()
            self.task_id = task_id
            self.elapsed_seconds = elapsed_seconds

    class TimerPaused(Message):
        """Posted when timer is paused."""

        pass

    class TimerResumed(Message):
        """Posted when timer is resumed."""

        pass

    def __init__(self, compact: bool = False) -> None:
        """Initialize the timer display.

        Args:
            compact: If True, use a more compact layout
        """
        super().__init__()
        self._compact = compact
        self._timer_handle = None
        self._start_time: datetime | None = None
        self._pause_offset: int = 0

    def compose(self) -> ComposeResult:
        yield Static("", id="timer-status", classes="idle-indicator")

        if self._compact:
            yield Static("00:00:00", id="timer-digits-compact")
        else:
            yield Digits("00:00:00", id="timer-digits")

        yield Static("No active timer", id="timer-task-name")

        with Horizontal(id="timer-controls"):
            yield Button("▶ Start", variant="success", id="timer-start-btn")
            yield Button("⏸ Pause", variant="warning", id="timer-pause-btn", disabled=True)
            yield Button("⏹ Stop", variant="error", id="timer-stop-btn", disabled=True)

    def on_mount(self) -> None:
        """Initialize timer on mount."""
        self._check_active_timer()

    def _check_active_timer(self) -> None:
        """Check for an existing active timer in the database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.time_entry import get_active_timer

            with get_db() as db:
                active = get_active_timer(db)
                if active:
                    self.task_id = active.node_id
                    self._start_time = active.start_time

                    # Calculate elapsed time
                    if self._start_time:
                        elapsed = datetime.now() - self._start_time
                        self.elapsed_seconds = int(elapsed.total_seconds())

                    # Get task name
                    from taskyn.graph.nodes import get_node

                    task = get_node(db, active.node_id)
                    if task:
                        self.task_name = task.title

                    self.is_running = True
                    self._start_tick()

        except Exception:
            pass

    def _start_tick(self) -> None:
        """Start the timer tick."""
        if self._timer_handle is None:
            self._timer_handle = self.set_interval(1, self._tick)

    def _stop_tick(self) -> None:
        """Stop the timer tick."""
        if self._timer_handle:
            self._timer_handle.stop()
            self._timer_handle = None

    def _tick(self) -> None:
        """Called every second while timer is running."""
        if self.is_running and not self.is_paused:
            self.elapsed_seconds += 1

    def watch_elapsed_seconds(self, elapsed: int) -> None:
        """Update display when elapsed time changes."""
        time_str = self._format_time(elapsed)

        if self._compact:
            digits = self.query_one("#timer-digits-compact", Static)
            digits.update(time_str)
        else:
            digits = self.query_one("#timer-digits", Digits)
            digits.update(time_str)

    def watch_is_running(self, running: bool) -> None:
        """Update UI when running state changes."""
        start_btn = self.query_one("#timer-start-btn", Button)
        pause_btn = self.query_one("#timer-pause-btn", Button)
        stop_btn = self.query_one("#timer-stop-btn", Button)
        status = self.query_one("#timer-status", Static)

        if running:
            start_btn.disabled = True
            pause_btn.disabled = False
            stop_btn.disabled = False
            status.update("● RECORDING")
            status.set_classes("recording-indicator")
        else:
            start_btn.disabled = False
            pause_btn.disabled = True
            stop_btn.disabled = True
            status.update("")
            status.set_classes("idle-indicator")

    def watch_is_paused(self, paused: bool) -> None:
        """Update UI when paused state changes."""
        if not self.is_running:
            return

        pause_btn = self.query_one("#timer-pause-btn", Button)
        status = self.query_one("#timer-status", Static)

        if paused:
            pause_btn.label = "▶ Resume"
            status.update("⏸ PAUSED")
            status.set_classes("paused-indicator")
        else:
            pause_btn.label = "⏸ Pause"
            status.update("● RECORDING")
            status.set_classes("recording-indicator")

    def watch_task_name(self, name: str) -> None:
        """Update task name display."""
        label = self.query_one("#timer-task-name", Static)
        if name:
            label.update(name)
        else:
            label.update("No active timer")

    def _format_time(self, seconds: int) -> str:
        """Format seconds as HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "timer-start-btn":
            # Can't start without a task - notify user
            self.app.notify("Select a task first, then press 't' to start timer", title="No Task")
        elif event.button.id == "timer-pause-btn":
            self.toggle_pause()
        elif event.button.id == "timer-stop-btn":
            self.stop_timer()

    def start_timer(self, task_id: str, task_name: str) -> None:
        """Start timing a task."""
        if self.is_running:
            # Stop current timer first
            self.stop_timer()

        self.task_id = task_id
        self.task_name = task_name
        self.elapsed_seconds = 0
        self.is_paused = False
        self._start_time = datetime.now()
        self._pause_offset = 0

        # Start in database
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.time_entry import start_timer

            with get_db() as db:
                start_timer(db, task_id)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Timer Error", severity="error")
            return

        self.is_running = True
        self._start_tick()
        self.post_message(self.TimerStarted(task_id))

    def stop_timer(self) -> None:
        """Stop the timer and save time entry."""
        if not self.is_running:
            return

        task_id = self.task_id
        elapsed = self.elapsed_seconds

        self._stop_tick()

        # Save in database
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.time_entry import stop_timer

            with get_db() as db:
                stop_timer(db, task_id)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Timer Error", severity="error")

        # Reset state
        self.is_running = False
        self.is_paused = False
        self.task_id = None
        self.task_name = "No active timer"
        self.elapsed_seconds = 0
        self._start_time = None
        self._pause_offset = 0

        self.post_message(self.TimerStopped(task_id, elapsed))

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if not self.is_running:
            return

        self.is_paused = not self.is_paused

        if self.is_paused:
            self.post_message(self.TimerPaused())
        else:
            self.post_message(self.TimerResumed())

    def get_state(self) -> dict[str, Any]:
        """Get current timer state for persistence."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "elapsed_seconds": self.elapsed_seconds,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
        }
