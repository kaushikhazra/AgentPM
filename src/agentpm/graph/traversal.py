"""Graph traversal algorithms."""

from collections import deque

from agentpm.db.connection import fetchall
from agentpm.db.models import Node
from agentpm.graph.nodes import get_node, _row_to_node


def detect_cycle(source_id: str, target_id: str, edge_type: str) -> bool:
    """
    Detect if adding an edge would create a cycle.

    Returns True if creating an edge from source_id to target_id
    would create a cycle. Uses DFS from target to see if source is reachable.
    """
    # If adding source -> target edge, check if target can reach source
    # (which would create a cycle)
    visited = set()
    stack = [target_id]

    while stack:
        current = stack.pop()
        if current == source_id:
            return True

        if current in visited:
            continue
        visited.add(current)

        # Get all nodes this current node points to (following edges of same type)
        rows = fetchall(
            "SELECT target_id FROM edges WHERE source_id = ? AND edge_type = ?",
            (current, edge_type),
        )
        for row in rows:
            if row["target_id"] not in visited:
                stack.append(row["target_id"])

    return False


def get_ancestors(
    node_id: str,
    edge_type: str | None = None,
    max_depth: int | None = None,
) -> list[Node]:
    """
    Get all ancestors of a node (nodes this node points to, recursively).

    For a 'parent' edge type, this returns the parent, grandparent, etc.
    Uses BFS to traverse up the graph.
    """
    ancestors = []
    visited = set()
    queue = deque([(node_id, 0)])

    while queue:
        current_id, depth = queue.popleft()

        if current_id in visited:
            continue
        visited.add(current_id)

        # Skip the starting node
        if current_id != node_id:
            node = get_node(current_id)
            if node:
                ancestors.append(node)

        # Check depth limit
        if max_depth is not None and depth >= max_depth:
            continue

        # Get all targets (ancestors) of current node
        sql = "SELECT target_id FROM edges WHERE source_id = ?"
        params = [current_id]

        if edge_type is not None:
            sql += " AND edge_type = ?"
            params.append(edge_type)

        rows = fetchall(sql, tuple(params))
        for row in rows:
            if row["target_id"] not in visited:
                queue.append((row["target_id"], depth + 1))

    return ancestors


def get_descendants(
    node_id: str,
    edge_type: str | None = None,
    max_depth: int | None = None,
) -> list[Node]:
    """
    Get all descendants of a node (nodes that point to this node, recursively).

    For a 'parent' edge type, this returns all children, grandchildren, etc.
    Uses BFS to traverse down the graph.
    """
    descendants = []
    visited = set()
    queue = deque([(node_id, 0)])

    while queue:
        current_id, depth = queue.popleft()

        if current_id in visited:
            continue
        visited.add(current_id)

        # Skip the starting node
        if current_id != node_id:
            node = get_node(current_id)
            if node:
                descendants.append(node)

        # Check depth limit
        if max_depth is not None and depth >= max_depth:
            continue

        # Get all sources (descendants/children) that point to current node
        sql = "SELECT source_id FROM edges WHERE target_id = ?"
        params = [current_id]

        if edge_type is not None:
            sql += " AND edge_type = ?"
            params.append(edge_type)

        rows = fetchall(sql, tuple(params))
        for row in rows:
            if row["source_id"] not in visited:
                queue.append((row["source_id"], depth + 1))

    return descendants


def get_parents(node_id: str, edge_type: str = "parent") -> list[Node]:
    """
    Get direct parents of a node (depth=1).

    These are the nodes that the given node points to.
    """
    return get_ancestors(node_id, edge_type=edge_type, max_depth=1)


def get_children(node_id: str, edge_type: str = "parent") -> list[Node]:
    """
    Get direct children of a node (depth=1).

    These are the nodes that point to the given node.
    """
    return get_descendants(node_id, edge_type=edge_type, max_depth=1)
