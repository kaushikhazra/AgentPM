"""Project tree widget for Taskyn TUI."""

from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


# Node type icons
NODE_ICONS = {
    "company": "🏢",
    "project": "📁",
    "milestone": "🎯",
    "story": "📖",
    "task": "✓",
    "spec": "📋",
    "design": "📐",
    "implementation": "⚙",
    "validation": "✅",
}


class ProjectTree(Tree):
    """Hierarchical view of projects and tasks."""

    class NodeSelected(Message):
        """Posted when a node is selected."""

        def __init__(self, node_id: str, node_type: str, node_name: str) -> None:
            super().__init__()
            self.node_id = node_id
            self.node_type = node_type
            self.node_name = node_name

    def __init__(self) -> None:
        super().__init__("Workspace", id="project-tree")
        self.show_root = False

    def on_mount(self) -> None:
        """Load project hierarchy when mounted."""
        self.root.expand()
        self.load_hierarchy()

    def load_hierarchy(self) -> None:
        """Load project hierarchy from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes
            from taskyn.graph.edges import get_children

            with get_db() as db:
                # Get all nodes
                nodes = list_nodes(db)
                nodes_by_id = {n.id: n for n in nodes}

                # Find root nodes (companies or projects without parents)
                root_nodes = []
                for node in nodes:
                    children_of = get_children(db, node.id, "parent")
                    if not children_of:
                        # This is a root node
                        root_nodes.append(node)

                # Sort by type then name
                type_order = {"company": 0, "project": 1, "milestone": 2, "story": 3, "task": 4}
                root_nodes.sort(key=lambda n: (type_order.get(n.node_type, 99), n.title))

                # Build tree recursively
                for node in root_nodes:
                    self._add_node_to_tree(db, self.root, node, nodes_by_id)

        except Exception as e:
            # Database might not exist or be empty
            self.root.add_leaf(
                "No projects yet",
                data={"id": None, "type": None, "name": "empty"},
            )

    def _add_node_to_tree(
        self, db, parent_tree_node: TreeNode, node, nodes_by_id: dict
    ) -> None:
        """Recursively add a node and its children to the tree."""
        from taskyn.graph.edges import get_children

        icon = NODE_ICONS.get(node.node_type, "•")
        label = f"{icon} {node.title}"

        # Get children
        child_edges = get_children(db, node.id, "parent")
        child_nodes = []
        for edge in child_edges:
            child = nodes_by_id.get(edge.to_node_id)
            if child:
                child_nodes.append(child)

        # Sort children
        type_order = {"milestone": 0, "story": 1, "spec": 2, "task": 3}
        child_nodes.sort(key=lambda n: (type_order.get(n.node_type, 99), n.title))

        node_data = {
            "id": node.id,
            "type": node.node_type,
            "name": node.title,
            "status": node.status,
        }

        if child_nodes:
            # Node with children
            tree_node = parent_tree_node.add(label, data=node_data, expand=False)
            for child in child_nodes:
                self._add_node_to_tree(db, tree_node, child, nodes_by_id)
        else:
            # Leaf node
            parent_tree_node.add_leaf(label, data=node_data)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection."""
        node_data = event.node.data
        if node_data and node_data.get("id"):
            self.post_message(
                self.NodeSelected(
                    node_id=node_data["id"],
                    node_type=node_data["type"],
                    node_name=node_data["name"],
                )
            )

    def refresh_tree(self) -> None:
        """Refresh the tree from database."""
        self.root.remove_children()
        self.load_hierarchy()
