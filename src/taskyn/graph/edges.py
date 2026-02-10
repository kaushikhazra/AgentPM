"""Edge CRUD operations for the graph layer."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from taskyn.db.connection import execute, fetchone, fetchall, commit
from taskyn.db.models import Edge
from taskyn.core.activity import log_activity
from taskyn.core.project import get_project
from taskyn.methodologies import get_methodology
from taskyn.exceptions import NotFoundError, ValidationError, CycleDetectedError, CardinalityError
from taskyn.graph.validation import validate_edge_creation
from taskyn.graph.nodes import get_node


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def create_edge(
    source_id: str,
    target_id: str,
    edge_type: str,
    properties: dict | None = None,
    actor: str | None = None,
) -> Edge:
    """Create a new edge between nodes."""
    # Get source and target nodes (supports prefix matching)
    source = get_node(source_id)
    if source is None:
        raise NotFoundError("node", source_id)
    source_id = source.id  # Use full ID

    target = get_node(target_id)
    if target is None:
        raise NotFoundError("node", target_id)
    target_id = target.id  # Use full ID

    # Verify same project
    if source.project_id != target.project_id:
        raise ValidationError("Cannot create edge between nodes in different projects")

    # Get methodology and validate
    project = get_project(source.project_id)
    methodology = get_methodology(project.methodology)

    errors = validate_edge_creation(source, target, edge_type, project.methodology)
    if errors:
        raise ValidationError("\n".join(errors))

    # Check cardinality constraints
    et = methodology.get_edge_type(edge_type)
    if et:
        if et.max_per_source is not None:
            existing_count = _count_edges_from_source(source_id, edge_type)
            if existing_count >= et.max_per_source:
                raise CardinalityError(
                    f"Node already has maximum {et.max_per_source} '{edge_type}' edge(s)",
                    edge_type,
                    et.max_per_source,
                )

        if et.max_per_target is not None:
            existing_count = _count_edges_to_target(target_id, edge_type)
            if existing_count >= et.max_per_target:
                raise CardinalityError(
                    f"Target node already has maximum {et.max_per_target} incoming '{edge_type}' edge(s)",
                    edge_type,
                    et.max_per_target,
                )

        # Check for cycles if not allowed
        if not et.allows_cycles:
            from taskyn.graph.traversal import detect_cycle
            if detect_cycle(source_id, target_id, edge_type):
                raise CycleDetectedError(source_id, target_id, edge_type)

    edge_id = uuid4().hex
    now = _now()
    properties_json = json.dumps(properties) if properties else None

    execute(
        """
        INSERT INTO edges (id, project_id, source_id, target_id, edge_type, properties, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (edge_id, source.project_id, source_id, target_id, edge_type, properties_json, now),
    )

    log_activity(
        entity_type="edge",
        entity_id=edge_id,
        action="created",
        new_value=f"{source_id} -> {target_id} ({edge_type})",
        actor=actor,
    )

    commit()

    # Propagate actual_time when parent hierarchy changes
    if edge_type == "parent":
        from taskyn.core.time_entry import propagate_actual_time
        propagate_actual_time(target_id)

    return Edge(
        id=edge_id,
        project_id=source.project_id,
        source_id=source_id,
        target_id=target_id,
        edge_type=edge_type,
        properties=properties,
        created_at=now,
    )


def get_edge(edge_id: str) -> Edge | None:
    """Get an edge by ID."""
    row = fetchone("SELECT * FROM edges WHERE id = ?", (edge_id,))
    if row is None:
        return None
    return _row_to_edge(row)


def list_edges(
    project_id: str | None = None,
    source_id: str | None = None,
    target_id: str | None = None,
    edge_type: str | None = None,
) -> list[Edge]:
    """List edges with optional filters."""
    sql = "SELECT * FROM edges WHERE 1=1"
    params = []

    if project_id is not None:
        sql += " AND project_id = ?"
        params.append(project_id)

    if source_id is not None:
        sql += " AND source_id = ?"
        params.append(source_id)

    if target_id is not None:
        sql += " AND target_id = ?"
        params.append(target_id)

    if edge_type is not None:
        sql += " AND edge_type = ?"
        params.append(edge_type)

    sql += " ORDER BY created_at"

    rows = fetchall(sql, tuple(params))
    return [_row_to_edge(row) for row in rows]


def delete_edge(edge_id: str, actor: str | None = None) -> bool:
    """Delete an edge."""
    edge = get_edge(edge_id)
    if edge is None:
        return False

    log_activity(
        entity_type="edge",
        entity_id=edge_id,
        action="deleted",
        old_value=f"{edge.source_id} -> {edge.target_id} ({edge.edge_type})",
        actor=actor,
    )

    execute("DELETE FROM edges WHERE id = ?", (edge_id,))
    commit()

    # Propagate actual_time when parent hierarchy changes
    if edge.edge_type == "parent":
        from taskyn.core.time_entry import propagate_actual_time
        propagate_actual_time(edge.target_id)

    return True


def _count_edges_from_source(source_id: str, edge_type: str) -> int:
    """Count edges of a type from a source node."""
    row = fetchone(
        "SELECT COUNT(*) as cnt FROM edges WHERE source_id = ? AND edge_type = ?",
        (source_id, edge_type),
    )
    return row["cnt"] if row else 0


def _count_edges_to_target(target_id: str, edge_type: str) -> int:
    """Count edges of a type to a target node."""
    row = fetchone(
        "SELECT COUNT(*) as cnt FROM edges WHERE target_id = ? AND edge_type = ?",
        (target_id, edge_type),
    )
    return row["cnt"] if row else 0


def _row_to_edge(row) -> Edge:
    """Convert a database row to an Edge model."""
    properties = None
    if row["properties"]:
        try:
            properties = json.loads(row["properties"])
        except json.JSONDecodeError:
            pass

    return Edge(
        id=row["id"],
        project_id=row["project_id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        edge_type=row["edge_type"],
        properties=properties,
        created_at=_parse_datetime(row["created_at"]),
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
