"""Tag list widget for displaying and managing tags."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Static


class TagList(Horizontal):
    """Display tags for a node with add/remove functionality."""

    class TagRemoved(Message):
        """Posted when a tag is removed."""

        def __init__(self, tag_name: str) -> None:
            super().__init__()
            self.tag_name = tag_name

    class AddTagRequested(Message):
        """Posted when add tag button is clicked."""

        pass

    def __init__(self, node_id: str, editable: bool = True) -> None:
        """Initialize the tag list.

        Args:
            node_id: ID of the node to show tags for
            editable: Whether to show add/remove buttons
        """
        super().__init__()
        self.node_id = node_id
        self.editable = editable
        self._tags = []

    def compose(self) -> ComposeResult:
        self._load_tags()

        if self._tags:
            for tag in self._tags:
                color = tag.color or "#6B7280"
                with Horizontal(classes="tag-chip"):
                    yield Static(f"[{color}]●[/] {tag.name}")
                    if self.editable:
                        yield Button("×", variant="default", classes="tag-remove", id=f"remove-{tag.id}")
        else:
            yield Static("[dim]No tags[/dim]", classes="no-tags")

        if self.editable:
            yield Button("+ Tag", variant="default", classes="add-tag-btn", id="add-tag-btn")

    def _load_tags(self) -> None:
        """Load tags from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import get_node_tags

            with get_db() as db:
                self._tags = get_node_tags(db, self.node_id)

        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-tag-btn":
            self.post_message(self.AddTagRequested())
        elif event.button.id and event.button.id.startswith("remove-"):
            tag_id = event.button.id.replace("remove-", "")
            # Find tag name
            for tag in self._tags:
                if tag.id == tag_id:
                    self._remove_tag(tag.name)
                    break

    def _remove_tag(self, tag_name: str) -> None:
        """Remove a tag from the node."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.core.tag import untag_node

            with get_db() as db:
                untag_node(db, self.node_id, tag_name)

            self.post_message(self.TagRemoved(tag_name))
            self.refresh_tags()

        except Exception as e:
            self.app.notify(f"Error removing tag: {e}", title="Error", severity="error")

    def refresh_tags(self) -> None:
        """Refresh the tag list."""
        self._tags = []
        self._load_tags()

        # Remove all children and recompose
        self.remove_children()

        if self._tags:
            for tag in self._tags:
                color = tag.color or "#6B7280"
                with Horizontal(classes="tag-chip"):
                    self.mount(Static(f"[{color}]●[/] {tag.name}"))
                    if self.editable:
                        self.mount(Button("×", variant="default", classes="tag-remove", id=f"remove-{tag.id}"))
        else:
            self.mount(Static("[dim]No tags[/dim]", classes="no-tags"))

        if self.editable:
            self.mount(Button("+ Tag", variant="default", classes="add-tag-btn", id="add-tag-btn"))
