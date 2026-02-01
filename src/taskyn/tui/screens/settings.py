"""Settings screen for Taskyn TUI."""

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RadioButton, RadioSet, Static


class SettingsScreen(Screen):
    """Settings configuration screen."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("1", "go_dashboard", "Dashboard", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(id="settings-content"):
            # Appearance Section
            with Vertical(classes="settings-section"):
                yield Static("Appearance", classes="section-title")

                with Horizontal(classes="setting-row"):
                    yield Label("Theme:", classes="setting-label")
                    with RadioSet(id="theme-select", classes="setting-value"):
                        yield RadioButton("Dark", id="theme-dark", value=True)
                        yield RadioButton("Light", id="theme-light")

            # Database Section
            with Vertical(classes="settings-section"):
                yield Static("Database", classes="section-title")

                db_path = self._get_db_path()
                db_size = self._get_db_size(db_path)

                yield Static(f"Path: {db_path}", classes="db-info")
                yield Static(f"Size: {db_size}", classes="db-info")

                with Horizontal(classes="button-row"):
                    yield Button("Backup Now", variant="primary", id="backup-btn")
                    yield Button("Export JSON", variant="default", id="export-btn")

            # Tags Section
            with Vertical(classes="settings-section"):
                yield Static("Tags", classes="section-title")

                yield Static(id="tags-list")

                with Horizontal(classes="button-row"):
                    yield Button("Create Tag", variant="primary", id="create-tag-btn")
                    yield Button("Refresh", variant="default", id="refresh-tags-btn")

            # About Section
            with Vertical(classes="settings-section"):
                yield Static("About", classes="section-title")

                yield Static("Taskyn - AI-First Project Management")
                yield Static("Version: 0.1.0", classes="db-info")
                yield Static("Built with Textual", classes="db-info")

            yield Static(
                "[dim]Press Escape to go back[/dim]",
                classes="version-info",
            )

        yield Footer()

    def on_mount(self) -> None:
        """Set initial theme selection."""
        is_dark = self.app.theme == "textual-dark"
        if is_dark:
            self.query_one("#theme-dark", RadioButton).value = True
        else:
            self.query_one("#theme-light", RadioButton).value = True

        # Load tags
        self._refresh_tags()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle theme change."""
        if event.radio_set.id == "theme-select":
            if event.pressed.id == "theme-dark":
                self.app.theme = "textual-dark"
            else:
                self.app.theme = "textual-light"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "backup-btn":
            self._do_backup()
        elif event.button.id == "export-btn":
            self._do_export()
        elif event.button.id == "create-tag-btn":
            self._create_tag()
        elif event.button.id == "refresh-tags-btn":
            self._refresh_tags()
        elif event.button.id and event.button.id.startswith("delete-tag-"):
            tag_id = event.button.id.replace("delete-tag-", "")
            self._delete_tag(tag_id)

    def _get_db_path(self) -> str:
        """Get the database path."""
        try:
            from taskyn.config import get_db_path

            return str(get_db_path())
        except Exception:
            return "~/.taskyn/taskyn.db"

    def _get_db_size(self, path: str) -> str:
        """Get database file size."""
        try:
            expanded = Path(path).expanduser()
            if expanded.exists():
                size = expanded.stat().st_size
                if size < 1024:
                    return f"{size} bytes"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
            return "Not created yet"
        except Exception:
            return "Unknown"

    def _do_backup(self) -> None:
        """Create a database backup."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.config import get_db_path
            from datetime import datetime
            import shutil

            db_path = Path(get_db_path())
            if db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = db_path.parent / f"taskyn_backup_{timestamp}.db"
                shutil.copy2(db_path, backup_path)
                self.app.notify(f"Backup created: {backup_path.name}", title="Backup")
            else:
                self.app.notify("No database to backup", title="Backup", severity="warning")

        except Exception as e:
            self.app.notify(f"Backup failed: {e}", title="Error", severity="error")

    def _do_export(self) -> None:
        """Export data as JSON."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes
            from taskyn.config import get_db_path
            from datetime import datetime
            import json

            with get_db() as db:
                nodes = list_nodes(db)

                data = {
                    "exported_at": datetime.now().isoformat(),
                    "version": "0.1.0",
                    "nodes": [
                        {
                            "id": n.id,
                            "type": n.node_type,
                            "title": n.title,
                            "status": n.status,
                            "description": n.description,
                            "metadata": n.metadata,
                        }
                        for n in nodes
                    ],
                }

            # Save to file
            db_path = Path(get_db_path())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = db_path.parent / f"taskyn_export_{timestamp}.json"

            with open(export_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            self.app.notify(f"Exported: {export_path.name}", title="Export")

        except Exception as e:
            self.app.notify(f"Export failed: {e}", title="Error", severity="error")

    def action_go_dashboard(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()

    def _refresh_tags(self) -> None:
        """Refresh the tags list."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import list_tags

            with get_db() as db:
                tags = list_tags(db)

            tags_display = self.query_one("#tags-list", Static)

            if tags:
                tag_lines = []
                for tag in tags:
                    color = tag.color or "#6B7280"
                    tag_lines.append(f"[{color}]●[/] {tag.name}")
                tags_display.update("\n".join(tag_lines))
            else:
                tags_display.update("[dim]No tags created yet[/dim]")

        except Exception as e:
            tags_display = self.query_one("#tags-list", Static)
            tags_display.update(f"[red]Error loading tags: {e}[/red]")

    def _create_tag(self) -> None:
        """Open tag creation dialog."""
        from taskyn.tui.dialogs.tag_form import TagFormModal

        def on_dismiss(created: bool) -> None:
            if created:
                self._refresh_tags()

        self.app.push_screen(TagFormModal(), on_dismiss)

    def _delete_tag(self, tag_id: str) -> None:
        """Delete a tag."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import delete_tag

            with get_db() as db:
                delete_tag(db, tag_id)

            self.app.notify("Tag deleted", title="Deleted")
            self._refresh_tags()

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")
