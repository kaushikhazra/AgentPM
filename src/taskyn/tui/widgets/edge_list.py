"""Edge list widget for displaying node relationships."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static


class EdgeList(Vertical):
    """Display edges (relationships) for a node."""

    class EdgeClicked(Message):
        """Posted when an edge target is clicked."""

        def __init__(self, node_id: str, node_type: str, node_title: str) -> None:
            super().__init__()
            self.node_id = node_id
            self.node_type = node_type
            self.node_title = node_title

    def __init__(self, node_id: str, show_header: bool = True) -> None:
        """Initialize the edge list.

        Args:
            node_id: ID of the node to show edges for
            show_header: Whether to show section header
        """
        super().__init__()
        self.node_id = node_id
        self.show_header = show_header
        self._parents = []
        self._children = []
        self._blocking = []
        self._blocked_by = []

    def compose(self) -> ComposeResult:
        self._load_edges()

        if self.show_header:
            yield Static("Relationships", classes="section-header")

        # Parents
        if self._parents:
            yield Static("[dim]Parent of:[/dim]")
            for node in self._parents:
                icon = self._get_icon(node.node_type)
                yield Static(f"  {icon} {node.title}", classes="edge-item")

        # Children
        if self._children:
            yield Static("[dim]Children:[/dim]")
            for node in self._children:
                icon = self._get_icon(node.node_type)
                status_icon = self._get_status_icon(node.status)
                yield Static(f"  {icon} {status_icon} {node.title}", classes="edge-item")

        # Blocking
        if self._blocking:
            yield Static("[dim]Blocking:[/dim]")
            for node in self._blocking:
                icon = self._get_icon(node.node_type)
                yield Static(f"  {icon} {node.title}", classes="edge-item")

        # Blocked by
        if self._blocked_by:
            yield Static("[red]Blocked by:[/red]")
            for node in self._blocked_by:
                icon = self._get_icon(node.node_type)
                yield Static(f"  {icon} {node.title}", classes="edge-item")

        if not any([self._parents, self._children, self._blocking, self._blocked_by]):
            yield Static("[dim]No relationships[/dim]", classes="no-edges")

    def _load_edges(self) -> None:
        """Load edges from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.edges import list_edges
            from taskyn.graph.nodes import get_node

            with get_db() as db:
                # Get all edges involving this node
                edges = list_edges(db, source_id=self.node_id) + list_edges(db, target_id=self.node_id)

                for edge in edges:
                    if edge.edge_type == "parent":
                        if edge.source_id == self.node_id:
                            # This node is parent to target
                            child = get_node(db, edge.target_id)
                            if child:
                                self._children.append(child)
                        else:
                            # This node is child of source
                            parent = get_node(db, edge.source_id)
                            if parent:
                                self._parents.append(parent)

                    elif edge.edge_type == "blocks":
                        if edge.source_id == self.node_id:
                            # This node blocks target
                            blocked = get_node(db, edge.target_id)
                            if blocked:
                                self._blocking.append(blocked)
                        else:
                            # This node is blocked by source
                            blocker = get_node(db, edge.source_id)
                            if blocker:
                                self._blocked_by.append(blocker)

        except Exception:
            pass

    def _get_icon(self, node_type: str) -> str:
        """Get icon for node type."""
        icons = {
            "company": "🏢",
            "project": "📁",
            "milestone": "🎯",
            "story": "📖",
            "task": "✓",
            "spec": "📋",
        }
        return icons.get(node_type, "•")

    def _get_status_icon(self, status: str) -> str:
        """Get icon for status."""
        icons = {
            "backlog": "○",
            "ready": "●",
            "in_progress": "[yellow]◐[/]",
            "done": "[green]✓[/]",
            "blocked": "[red]✗[/]",
        }
        return icons.get(status, "")

    def refresh_edges(self) -> None:
        """Refresh the edge list."""
        self._parents = []
        self._children = []
        self._blocking = []
        self._blocked_by = []
        self._load_edges()
        self.refresh()
