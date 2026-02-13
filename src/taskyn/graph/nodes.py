"""Node CRUD operations for the graph layer."""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from taskyn.db.connection import execute, fetchone, fetchall, commit
from taskyn.db.models import Node
from taskyn.core.activity import log_activity
from taskyn.core.project import get_project
from taskyn.methodologies import get_methodology
from taskyn.exceptions import NotFoundError, ValidationError
from taskyn.graph.validation import validate_node_creation, validate_node_update


# Sentinel value for "not provided" vs explicit None
class _Unset:
    """Sentinel for unset optional parameters."""
    pass

UNSET: Any = _Unset()


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def create_node(
    project_id: str,
    node_type: str,
    title: str,
    description: str | None = None,
    assignee: str | None = None,
    milestone_id: str | None = None,
    estimated_minutes: int | None = None,
    story_points: int | None = None,
    priority: str = "medium",
    properties: dict | None = None,
    actor: str | None = None,
) -> Node:
    """Create a new node in the graph."""
    # Get project and validate (supports prefix matching)
    project = get_project(project_id)
    if project is None:
        raise NotFoundError("project", project_id)
    project_id = project.id  # Use full resolved ID

    # Validate node creation
    errors = validate_node_creation(project_id, node_type, project.methodology, properties)
    if errors:
        raise ValidationError("\n".join(errors))

    # Get initial status from methodology
    methodology = get_methodology(project.methodology)
    initial_status = methodology.get_initial_status(node_type)

    node_id = uuid4().hex
    now = _now()
    properties_json = json.dumps(properties) if properties else None

    execute(
        """
        INSERT INTO nodes (
            id, project_id, milestone_id, node_type, title, description,
            status, assignee, estimated_minutes, story_points, priority,
            properties, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            node_id, project_id, milestone_id, node_type, title, description,
            initial_status, assignee, estimated_minutes, story_points, priority,
            properties_json, now, now,
        ),
    )

    log_activity(
        entity_type="node",
        entity_id=node_id,
        action="created",
        new_value=title,
        node_type=node_type,
        actor=actor,
    )

    commit()

    return Node(
        id=node_id,
        project_id=project_id,
        milestone_id=milestone_id,
        node_type=node_type,
        title=title,
        description=description,
        status=initial_status,
        assignee=assignee,
        estimated_minutes=estimated_minutes,
        story_points=story_points,
        priority=priority or "medium",
        properties=properties,
        created_at=now,
        updated_at=now,
        completed_at=None,
    )


def get_node(node_id: str) -> Node | None:
    """Get a node by ID (supports prefix matching)."""
    # Try exact match first
    row = fetchone("SELECT * FROM nodes WHERE id = ?", (node_id,))

    # If not found, try prefix match
    if row is None and len(node_id) >= 4:
        rows = fetchall(
            "SELECT * FROM nodes WHERE id LIKE ?",
            (node_id + "%",),
        )
        if len(rows) == 1:
            row = rows[0]

    if row is None:
        return None
    return _row_to_node(row)


def list_nodes(
    project_id: str | None = None,
    node_type: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    milestone_id: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Node]:
    """List nodes with optional filters."""
    sql = "SELECT * FROM nodes WHERE 1=1"
    params = []

    if project_id is not None:
        sql += " AND project_id = ?"
        params.append(project_id)

    if node_type is not None:
        sql += " AND node_type = ?"
        params.append(node_type)

    if status is not None:
        sql += " AND status = ?"
        params.append(status)

    if assignee is not None:
        sql += " AND assignee = ?"
        params.append(assignee)

    if milestone_id is not None:
        sql += " AND milestone_id = ?"
        params.append(milestone_id)

    sql += " ORDER BY created_at DESC"
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = fetchall(sql, tuple(params))
    return [_row_to_node(row) for row in rows]


def update_node(
    node_id: str,
    title: str | None = None,
    description: str | None = None,
    status: str | None = None,
    assignee: str | None | _Unset = UNSET,
    milestone_id: str | None | _Unset = UNSET,
    estimated_minutes: int | None = None,
    story_points: int | None = None,
    priority: str | None = None,
    blocked_reason: str | None | _Unset = UNSET,
    properties: dict | None = None,
    actor: str | None = None,
) -> Node:
    """Update a node (supports prefix matching)."""
    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)
    node_id = node.id  # Use full ID

    project = get_project(node.project_id)
    methodology = get_methodology(project.methodology)

    # Validate updates (convert UNSET to None for validation)
    validate_blocked_reason = None if isinstance(blocked_reason, _Unset) else blocked_reason
    errors = validate_node_update(node, project.methodology, status, validate_blocked_reason)
    if errors:
        raise ValidationError("\n".join(errors))

    now = _now()
    updates = []
    params = []

    if title is not None and title != node.title:
        updates.append("title = ?")
        params.append(title)

    if description is not None and description != node.description:
        updates.append("description = ?")
        params.append(description)

    if status is not None and status != node.status:
        updates.append("status = ?")
        params.append(status)
        log_activity(
            entity_type="node",
            entity_id=node_id,
            action="status_changed",
            old_value=node.status,
            new_value=status,
            node_type=node.node_type,
            actor=actor,
        )
        # Set completed_at if entering terminal status
        if methodology.is_terminal_status(node.node_type, status):
            updates.append("completed_at = ?")
            params.append(now)

    if not isinstance(assignee, _Unset) and assignee != node.assignee:
        updates.append("assignee = ?")
        params.append(assignee)
        log_activity(
            entity_type="node",
            entity_id=node_id,
            action="assigned" if assignee else "unassigned",
            old_value=node.assignee,
            new_value=assignee,
            node_type=node.node_type,
            actor=actor,
        )

    if not isinstance(milestone_id, _Unset) and milestone_id != node.milestone_id:
        updates.append("milestone_id = ?")
        params.append(milestone_id)

    if estimated_minutes is not None:
        updates.append("estimated_minutes = ?")
        params.append(estimated_minutes)

    if story_points is not None:
        updates.append("story_points = ?")
        params.append(story_points)

    if priority is not None and priority != node.priority:
        updates.append("priority = ?")
        params.append(priority)

    if not isinstance(blocked_reason, _Unset):
        updates.append("blocked_reason = ?")
        params.append(blocked_reason if blocked_reason else None)

    if properties is not None:
        updates.append("properties = ?")
        params.append(json.dumps(properties))

    if not updates:
        return node

    updates.append("updated_at = ?")
    params.append(now)
    params.append(node_id)

    old_status = node.status
    new_status_value = status if (status is not None and status != node.status) else None

    execute(
        f"UPDATE nodes SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    commit()

    # Post-transition hook: verification failure cascade
    if new_status_value is not None:
        from taskyn.core.cascade import on_status_changed
        on_status_changed(node_id, node.node_type, old_status, new_status_value)

    return get_node(node_id)


def delete_node(node_id: str, actor: str | None = None) -> bool:
    """Delete a node (supports prefix matching)."""
    node = get_node(node_id)
    if node is None:
        return False
    node_id = node.id  # Use full ID

    log_activity(
        entity_type="node",
        entity_id=node_id,
        action="deleted",
        old_value=node.title,
        node_type=node.node_type,
        actor=actor,
    )

    execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    commit()

    return True


def _row_to_node(row) -> Node:
    """Convert a database row to a Node model."""
    properties = None
    if row["properties"]:
        try:
            properties = json.loads(row["properties"])
        except json.JSONDecodeError:
            pass

    return Node(
        id=row["id"],
        project_id=row["project_id"],
        milestone_id=row["milestone_id"],
        node_type=row["node_type"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        assignee=row["assignee"],
        estimated_minutes=row["estimated_minutes"],
        story_points=row["story_points"],
        actual_time=row["actual_time"],
        priority=row["priority"] or "medium",
        blocked_reason=row["blocked_reason"],
        properties=properties,
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
        completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
    )


def _parse_datetime(value) -> datetime:
    """Parse a datetime from SQLite."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ["%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return _now()
