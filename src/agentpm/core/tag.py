"""Tag system operations."""

from uuid import uuid4

from agentpm.db.connection import execute, fetchone, fetchall, commit
from agentpm.db.models import Tag, Node
from agentpm.core.activity import log_activity
from agentpm.exceptions import NotFoundError, ValidationError


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

    execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    commit()

    return True


def tag_node(node_id: str, tag_name: str, actor: str | None = None) -> None:
    """Add a tag to a node."""
    from agentpm.graph.nodes import get_node

    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)

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
    """Remove a tag from a node. Returns True if tag was removed."""
    from agentpm.graph.nodes import get_node

    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)

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
    """Get all tags for a node."""
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
    from agentpm.graph.nodes import _row_to_node

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
