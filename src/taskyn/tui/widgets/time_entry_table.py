"""Time entry table widget."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static


class TimeEntryTable(Vertical):
    """Display time entries for a node."""

    DEFAULT_CSS = """
    TimeEntryTable {
        height: auto;
        max-height: 15;
        padding: 0 1;
    }

    TimeEntryTable .section-header {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    TimeEntryTable .total-row {
        text-style: bold;
        padding-top: 1;
    }

    TimeEntryTable .no-entries {
        color: $text-muted;
    }

    TimeEntryTable DataTable {
        height: auto;
        max-height: 10;
    }
    """

    def __init__(self, node_id: str, show_header: bool = True) -> None:
        """Initialize the time entry table.

        Args:
            node_id: ID of the node to show time entries for
            show_header: Whether to show section header
        """
        super().__init__()
        self.node_id = node_id
        self.show_header = show_header
        self._entries = []
        self._total_minutes = 0

    def compose(self) -> ComposeResult:
        self._load_entries()

        if self.show_header:
            total_str = self._format_duration(self._total_minutes)
            yield Static(f"Time Entries ({total_str} total)", classes="section-header")

        if self._entries:
            table = DataTable(id="time-entries-table")
            table.add_columns("Date", "Duration", "Notes")
            yield table
        else:
            yield Static("[dim]No time entries[/dim]", classes="no-entries")

    def on_mount(self) -> None:
        """Populate table after mount."""
        if self._entries:
            table = self.query_one("#time-entries-table", DataTable)

            for entry in self._entries[:10]:  # Show last 10
                # Format date
                if entry.start_time:
                    date_str = entry.start_time.strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = "Unknown"

                # Format duration
                if entry.duration:
                    dur_minutes = int(entry.duration.total_seconds() // 60)
                    dur_str = self._format_duration(dur_minutes)
                else:
                    dur_str = "running..."

                # Notes (truncate)
                notes = entry.notes or ""
                if len(notes) > 30:
                    notes = notes[:27] + "..."

                table.add_row(date_str, dur_str, notes)

            if len(self._entries) > 10:
                table.add_row("...", f"+{len(self._entries) - 10} more", "")

    def _load_entries(self) -> None:
        """Load time entries from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.time_entry import get_time_entries

            with get_db() as db:
                self._entries = get_time_entries(db, self.node_id)

                # Calculate total
                self._total_minutes = 0
                for entry in self._entries:
                    if entry.duration:
                        self._total_minutes += int(entry.duration.total_seconds() // 60)

        except Exception:
            pass

    def _format_duration(self, minutes: int) -> str:
        """Format minutes as hours and minutes."""
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    def refresh_entries(self) -> None:
        """Refresh the time entries."""
        self._entries = []
        self._total_minutes = 0
        self._load_entries()
        self.refresh()
