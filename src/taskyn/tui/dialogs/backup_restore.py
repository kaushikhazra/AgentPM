"""Backup and restore dialog."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class BackupRestoreModal(ModalScreen[bool]):
    """Modal dialog for managing backups."""

    DEFAULT_CSS = """
    BackupRestoreModal {
        align: center middle;
    }

    #backup-dialog {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #backup-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    #backup-list {
        height: auto;
        max-height: 15;
        padding: 1;
        border: solid $surface-lighten-1;
    }

    .backup-item {
        height: auto;
        padding: 1;
        margin-bottom: 1;
        background: $surface-lighten-1;
    }

    .backup-item:hover {
        background: $surface-lighten-2;
    }

    .backup-name {
        text-style: bold;
    }

    .backup-info {
        color: $text-muted;
    }

    .no-backups {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }

    .button-row {
        margin-top: 1;
        height: auto;
        align: center middle;
    }

    .button-row Button {
        margin: 0 1;
    }

    .warning-text {
        color: $warning;
        text-align: center;
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._backups = []
        self._selected_backup: Path | None = None

    def compose(self) -> ComposeResult:
        self._load_backups()

        with Vertical(id="backup-dialog"):
            yield Static("Backup Manager", id="backup-title")

            yield Static(
                "[dim]Select a backup to restore, or create a new backup.[/dim]",
                classes="warning-text",
            )

            with VerticalScroll(id="backup-list"):
                if self._backups:
                    for backup in self._backups:
                        size = self._format_size(backup.stat().st_size)
                        mtime = backup.stat().st_mtime
                        from datetime import datetime
                        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

                        with Vertical(classes="backup-item"):
                            yield Static(f"{backup.name}", classes="backup-name")
                            yield Static(f"{date_str} - {size}", classes="backup-info")
                            with Horizontal():
                                yield Button("Restore", variant="warning", id=f"restore-{backup.name}")
                                yield Button("Delete", variant="error", id=f"delete-{backup.name}")
                else:
                    yield Static("No backups found", classes="no-backups")

            with Horizontal(classes="button-row"):
                yield Button("Create New Backup", variant="primary", id="create-backup-btn")
                yield Button("Close", variant="default", id="close-btn")

    def _load_backups(self) -> None:
        """Load list of existing backups."""
        try:
            from taskyn.config import get_db_path

            db_path = Path(get_db_path())
            backup_dir = db_path.parent

            # Find all backup files
            self._backups = sorted(
                backup_dir.glob("taskyn_backup_*.db"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

        except Exception:
            self._backups = []

    def _format_size(self, size: int) -> str:
        """Format file size."""
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-backup-btn":
            self._create_backup()
        elif event.button.id == "close-btn":
            self.dismiss(False)
        elif event.button.id and event.button.id.startswith("restore-"):
            backup_name = event.button.id.replace("restore-", "")
            self._confirm_restore(backup_name)
        elif event.button.id and event.button.id.startswith("delete-"):
            backup_name = event.button.id.replace("delete-", "")
            self._delete_backup(backup_name)

    def _create_backup(self) -> None:
        """Create a new backup."""
        try:
            from taskyn.config import get_db_path
            from datetime import datetime
            import shutil

            db_path = Path(get_db_path())
            if db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = db_path.parent / f"taskyn_backup_{timestamp}.db"
                shutil.copy2(db_path, backup_path)

                self.app.notify(f"Backup created: {backup_path.name}", title="Backup Created")
                self._refresh_list()
            else:
                self.app.notify("No database to backup", title="Error", severity="warning")

        except Exception as e:
            self.app.notify(f"Backup failed: {e}", title="Error", severity="error")

    def _confirm_restore(self, backup_name: str) -> None:
        """Confirm and restore from backup."""
        from taskyn.tui.dialogs.confirm import ConfirmDialog

        def on_dismiss(confirmed: bool) -> None:
            if confirmed:
                self._restore_backup(backup_name)

        self.app.push_screen(
            ConfirmDialog(
                message=f"Restore from '{backup_name}'?\n\nThis will replace your current database.\nA backup of the current database will be created first.",
                title="Restore Backup",
                confirm_label="Restore",
                cancel_label="Cancel",
                destructive=True,
            ),
            on_dismiss,
        )

    def _restore_backup(self, backup_name: str) -> None:
        """Restore from a backup."""
        try:
            from taskyn.config import get_db_path
            from datetime import datetime
            import shutil

            db_path = Path(get_db_path())
            backup_dir = db_path.parent
            backup_path = backup_dir / backup_name

            if not backup_path.exists():
                self.app.notify("Backup file not found", title="Error", severity="error")
                return

            # Create a backup of current database first
            if db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pre_restore_backup = backup_dir / f"taskyn_pre_restore_{timestamp}.db"
                shutil.copy2(db_path, pre_restore_backup)

            # Restore the backup
            shutil.copy2(backup_path, db_path)

            self.app.notify(f"Restored from: {backup_name}", title="Restored")
            self.app._refresh_dashboard()
            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Restore failed: {e}", title="Error", severity="error")

    def _delete_backup(self, backup_name: str) -> None:
        """Delete a backup file."""
        from taskyn.tui.dialogs.confirm import ConfirmDialog

        def on_dismiss(confirmed: bool) -> None:
            if confirmed:
                self._do_delete_backup(backup_name)

        self.app.push_screen(
            ConfirmDialog(
                message=f"Delete backup '{backup_name}'?\n\nThis cannot be undone.",
                title="Delete Backup",
                confirm_label="Delete",
                cancel_label="Cancel",
                destructive=True,
            ),
            on_dismiss,
        )

    def _do_delete_backup(self, backup_name: str) -> None:
        """Actually delete the backup file."""
        try:
            from taskyn.config import get_db_path

            db_path = Path(get_db_path())
            backup_path = db_path.parent / backup_name

            if backup_path.exists():
                backup_path.unlink()
                self.app.notify(f"Deleted: {backup_name}", title="Deleted")
                self._refresh_list()
            else:
                self.app.notify("Backup file not found", title="Error", severity="error")

        except Exception as e:
            self.app.notify(f"Delete failed: {e}", title="Error", severity="error")

    def _refresh_list(self) -> None:
        """Refresh the backup list."""
        self._load_backups()

        backup_list = self.query_one("#backup-list", VerticalScroll)
        backup_list.remove_children()

        if self._backups:
            for backup in self._backups:
                size = self._format_size(backup.stat().st_size)
                mtime = backup.stat().st_mtime
                from datetime import datetime
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

                with Vertical(classes="backup-item"):
                    backup_list.mount(Static(f"{backup.name}", classes="backup-name"))
                    backup_list.mount(Static(f"{date_str} - {size}", classes="backup-info"))
                    with Horizontal():
                        backup_list.mount(Button("Restore", variant="warning", id=f"restore-{backup.name}"))
                        backup_list.mount(Button("Delete", variant="error", id=f"delete-{backup.name}"))
        else:
            backup_list.mount(Static("No backups found", classes="no-backups"))

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
