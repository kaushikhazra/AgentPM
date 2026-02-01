"""Tag picker modal dialog."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Static


class TagPickerModal(ModalScreen[list[str]]):
    """Modal dialog for selecting tags for a node."""

    DEFAULT_CSS = """
    TagPickerModal {
        align: center middle;
    }

    #tag-picker-dialog {
        width: 50;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #tag-picker-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    #tag-list {
        height: auto;
        max-height: 20;
        padding: 1;
    }

    .tag-item {
        height: auto;
        padding: 0 1;
    }

    .no-tags {
        color: $text-muted;
        text-align: center;
        padding: 1;
    }

    .button-row {
        margin-top: 1;
        height: auto;
        align: center middle;
    }

    .button-row Button {
        margin: 0 1;
    }

    #create-tag-btn {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, node_id: str) -> None:
        """Initialize the modal.

        Args:
            node_id: ID of the node to manage tags for
        """
        super().__init__()
        self.node_id = node_id
        self._all_tags = []
        self._node_tags = []

    def compose(self) -> ComposeResult:
        self._load_tags()

        with Vertical(id="tag-picker-dialog"):
            yield Static("Manage Tags", id="tag-picker-title")

            with VerticalScroll(id="tag-list"):
                if self._all_tags:
                    for tag in self._all_tags:
                        is_selected = tag.id in [t.id for t in self._node_tags]
                        color = tag.color or "#6B7280"
                        with Horizontal(classes="tag-item"):
                            yield Checkbox(
                                f"[{color}]●[/] {tag.name}",
                                value=is_selected,
                                id=f"tag-{tag.id}",
                            )
                else:
                    yield Static("No tags created yet", classes="no-tags")

            yield Button("+ Create New Tag", variant="default", id="create-tag-btn")

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _load_tags(self) -> None:
        """Load all tags and current node's tags."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import list_tags, get_node_tags

            with get_db() as db:
                self._all_tags = list_tags(db)
                self._node_tags = get_node_tags(db, self.node_id)

        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            self._save_tags()
        elif event.button.id == "cancel-btn":
            self.dismiss([])
        elif event.button.id == "create-tag-btn":
            self._create_tag()

    def _create_tag(self) -> None:
        """Open tag creation dialog."""
        from taskyn.tui.dialogs.tag_form import TagFormModal

        def on_dismiss(created: bool) -> None:
            if created:
                # Refresh the tag list
                self._refresh_tags()

        self.app.push_screen(TagFormModal(), on_dismiss)

    def _refresh_tags(self) -> None:
        """Refresh the tag list after creating a new tag."""
        self._load_tags()

        tag_list = self.query_one("#tag-list", VerticalScroll)
        tag_list.remove_children()

        if self._all_tags:
            for tag in self._all_tags:
                is_selected = tag.id in [t.id for t in self._node_tags]
                color = tag.color or "#6B7280"
                with Horizontal(classes="tag-item"):
                    tag_list.mount(
                        Checkbox(
                            f"[{color}]●[/] {tag.name}",
                            value=is_selected,
                            id=f"tag-{tag.id}",
                        )
                    )
        else:
            tag_list.mount(Static("No tags created yet", classes="no-tags"))

    def _save_tags(self) -> None:
        """Save tag selections."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import tag_node, untag_node

            # Get selected tag IDs
            selected_ids = set()
            for tag in self._all_tags:
                checkbox = self.query_one(f"#tag-{tag.id}", Checkbox)
                if checkbox.value:
                    selected_ids.add(tag.id)

            # Get currently assigned tag IDs
            current_ids = {t.id for t in self._node_tags}

            with get_db() as db:
                # Add new tags
                for tag in self._all_tags:
                    if tag.id in selected_ids and tag.id not in current_ids:
                        tag_node(db, self.node_id, tag.name)

                # Remove unselected tags
                for tag in self._all_tags:
                    if tag.id not in selected_ids and tag.id in current_ids:
                        untag_node(db, self.node_id, tag.name)

            # Return list of selected tag names
            selected_names = [t.name for t in self._all_tags if t.id in selected_ids]
            self.app.notify(f"Tags updated", title="Tags Saved")
            self.dismiss(selected_names)

        except Exception as e:
            self.app.notify(f"Error: {e}", title="Failed", severity="error")

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss([])
