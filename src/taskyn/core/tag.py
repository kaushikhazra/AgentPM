"""Tag system operations."""

from uuid import uuid4

from taskyn.db.connection import execute, fetchone, fetchall, commit
from taskyn.db.models import Tag, Node
from taskyn.core.activity import log_activity
from taskyn.exceptions import NotFoundError, ValidationError


def create_tag(name: str, color: str | None = None) -> Tag:
    """Create a new tag."""
    # Check if tag already exists
    existing = get_tag_by_name(name)
    if existing is not None:
        raise ValidationError(f"Tag '{name}' already exists")

    tag_id = uuid4().hex

    execute(
        "INSERT INTO tags (id, name, color) VALUES (?, ?, ?)",
        (tag_id, name, color),
    )
    commit()

    return Tag(id=tag_id, name=name, color=color)


def get_tag(tag_id: str) -> Tag | None:
    """Get a tag by ID."""
    row = fetchone("SELECT * FROM tags WHERE id = ?", (tag_id,))
    if row is None:
        return None
    return Tag(id=row["id"], name=row["name"], color=row["color"])


def get_tag_by_name(name: str) -> Tag | None:
    """Get a tag by name."""
    row = fetchone("SELECT * FROM tags WHERE name = ?", (name,))
    if row is None:
        return None
    return Tag(id=row["id"], name=row["name"], color=row["color"])


def list_tags() -> list[Tag]:
    """List all tags."""
    rows = fetchall("SELECT * FROM tags ORDER BY name")
    return [Tag(id=row["id"], name=row["name"], color=row["color"]) for row in rows]


def delete_tag(tag_id: str) -> bool:
    """Delete a tag (removes from all nodes)."""
    tag = get_tag(tag_id)
    if tag is None:
        return False

    # Also delete from node_tags junction table
    execute("DELETE FROM node_tags WHERE tag_id = ?", (tag_id,))
    execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    commit()

    return True


def get_tag_usage_count(tag_name: str) -> int:
    """Get the number of nodes using a tag."""
    tag = get_tag_by_name(tag_name)
    if tag is None:
        return 0

    row = fetchone(
        "SELECT COUNT(*) as count FROM node_tags WHERE tag_id = ?",
        (tag.id,),
    )
    return row["count"] if row else 0


def delete_tag_by_name(tag_name: str) -> dict:
    """
    Delete a tag by name.

    Returns a dict with:
    - deleted: bool - whether the tag was deleted
    - usage_count: int - how many nodes were using the tag
    """
    tag = get_tag_by_name(tag_name)
    if tag is None:
        return {"deleted": False, "usage_count": 0}

    usage_count = get_tag_usage_count(tag_name)

    # Delete from node_tags junction table first
    execute("DELETE FROM node_tags WHERE tag_id = ?", (tag.id,))
    execute("DELETE FROM tags WHERE id = ?", (tag.id,))
    commit()

    return {"deleted": True, "usage_count": usage_count}


def tag_node(node_id: str, tag_name: str, actor: str | None = None) -> None:
    """Add a tag to a node (supports prefix matching)."""
    from taskyn.graph.nodes import get_node

    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)
    node_id = node.id  # Use full ID

    # Get or create tag
    tag = get_tag_by_name(tag_name)
    if tag is None:
        tag = create_tag(tag_name)

    # Check if already tagged
    row = fetchone(
        "SELECT 1 FROM node_tags WHERE node_id = ? AND tag_id = ?",
        (node_id, tag.id),
    )
    if row is not None:
        return  # Already tagged

    execute(
        "INSERT INTO node_tags (node_id, tag_id) VALUES (?, ?)",
        (node_id, tag.id),
    )

    log_activity(
        entity_type="node",
        entity_id=node_id,
        action="tagged",
        new_value=tag_name,
        node_type=node.node_type,
        actor=actor,
    )

    commit()


def untag_node(node_id: str, tag_name: str, actor: str | None = None) -> bool:
    """Remove a tag from a node (supports prefix matching). Returns True if tag was removed."""
    from taskyn.graph.nodes import get_node

    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)
    node_id = node.id  # Use full ID

    tag = get_tag_by_name(tag_name)
    if tag is None:
        return False  # Tag doesn't exist, nothing to remove

    # Check if tag is on node
    row = fetchone(
        "SELECT 1 FROM node_tags WHERE node_id = ? AND tag_id = ?",
        (node_id, tag.id),
    )
    if row is None:
        return False  # Tag not on node

    execute(
        "DELETE FROM node_tags WHERE node_id = ? AND tag_id = ?",
        (node_id, tag.id),
    )

    log_activity(
        entity_type="node",
        entity_id=node_id,
        action="untagged",
        old_value=tag_name,
        node_type=node.node_type,
        actor=actor,
    )

    commit()
    return True


def get_node_tags(node_id: str) -> list[Tag]:
    """Get all tags for a node (supports prefix matching)."""
    from taskyn.graph.nodes import get_node

    node = get_node(node_id)
    if node is None:
        return []
    node_id = node.id  # Use full ID

    rows = fetchall(
        """
        SELECT t.* FROM tags t
        JOIN node_tags nt ON t.id = nt.tag_id
        WHERE nt.node_id = ?
        ORDER BY t.name
        """,
        (node_id,),
    )
    return [Tag(id=row["id"], name=row["name"], color=row["color"]) for row in rows]


def list_nodes_by_tag(tag_name: str) -> list[Node]:
    """List all nodes with a specific tag."""
    from taskyn.graph.nodes import _row_to_node

    tag = get_tag_by_name(tag_name)
    if tag is None:
        return []

    rows = fetchall(
        """
        SELECT n.* FROM nodes n
        JOIN node_tags nt ON n.id = nt.node_id
        WHERE nt.tag_id = ?
        ORDER BY n.created_at DESC
        """,
        (tag.id,),
    )
    return [_row_to_node(row) for row in rows]
