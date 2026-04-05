"""Time tracking operations."""

from datetime import datetime, timezone
from uuid import uuid4

from taskyn.db.connection import execute, fetchone, fetchall, commit, serialized
from taskyn.db.models import TimeEntry
from taskyn.core.activity import log_activity
from taskyn.exceptions import NotFoundError, ValidationError


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def _enforce_time_tracking(node) -> None:
    """Raise ValidationError if the node's methodology disallows time tracking."""
    from taskyn.core.project import get_project
    from taskyn.methodologies import get_methodology

    project = get_project(node.project_id)
    if project is None:
        return  # Can't validate without project

    methodology = get_methodology(project.methodology)
    if methodology is None:
        return

    node_type_def = methodology.get_node_type(node.node_type)
    if node_type_def is not None and not node_type_def.can_track_time:
        raise ValidationError(
            f"Time tracking is not allowed on '{node.node_type}' nodes"
        )


def start_timer(
    node_id: str,
    notes: str | None = None,
    source: str = "manual",
    actor: str | None = None,
) -> TimeEntry:
    """
    Start a timer on a node (supports prefix matching).

    If this actor already has a running timer, it will be automatically stopped.
    Other actors' timers are not affected.
    """
    # Normalize empty string actor to None (D9)
    actor = actor or None

    # Verify node exists
    from taskyn.graph.nodes import get_node
    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)
    node_id = node.id  # Use full ID

    # Enforce can_track_time
    _enforce_time_tracking(node)

    with serialized():
        # Stop this actor's active timer (not global)
        active = get_active_timer(actor=actor)
        if active is not None:
            stop_timer(entry_id=active.id, actor=actor)

        entry_id = uuid4().hex
        now = _now()

        execute(
            """
            INSERT INTO time_entries (id, node_id, started_at, notes, source, actor, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (entry_id, node_id, now, notes, source, actor, now),
        )

        log_activity(
            entity_type="time_entry",
            entity_id=entry_id,
            action="time_started",
            new_value=node_id,
            node_type=node.node_type,
            actor=actor,
        )

        commit()

    return TimeEntry(
        id=entry_id,
        node_id=node_id,
        started_at=now,
        ended_at=None,
        duration_minutes=None,
        notes=notes,
        source=source,
        actor=actor,
        created_at=now,
    )


def stop_timer(
    node_id: str | None = None,
    entry_id: str | None = None,
    actor: str | None = None,
) -> TimeEntry | None:
    """
    Stop a running timer.

    If entry_id is provided, stop that specific entry.
    If node_id is provided, stop the active timer on that node.
    Otherwise, stop any active timer.
    """
    # Find the timer to stop
    if entry_id is not None:
        entry = _get_time_entry(entry_id)        # No actor check (D4)
    elif node_id is not None:
        entry = _get_active_timer_for_node(node_id, actor=actor)
    else:
        entry = get_active_timer(actor=actor)

    if entry is None:
        return None

    if entry.ended_at is not None:
        return entry  # Already stopped

    with serialized():
        now = _now()
        duration = int((now - entry.started_at).total_seconds() / 60)

        execute(
            "UPDATE time_entries SET ended_at = ?, duration_minutes = ? WHERE id = ?",
            (now, duration, entry.id),
        )

        log_activity(
            entity_type="time_entry",
            entity_id=entry.id,
            action="time_stopped",
            new_value=str(duration),
            actor=actor,
        )

        commit()

        propagate_actual_time(entry.node_id)

    return TimeEntry(
        id=entry.id,
        node_id=entry.node_id,
        started_at=entry.started_at,
        ended_at=now,
        duration_minutes=duration,
        notes=entry.notes,
        source=entry.source,
        actor=entry.actor,
        created_at=entry.created_at,
    )


def log_time(
    node_id: str,
    duration_minutes: int,
    notes: str | None = None,
    source: str = "manual",
    actor: str | None = None,
) -> TimeEntry:
    """Log a manual time entry (no timer, just duration). Supports prefix matching."""
    # Normalize empty string actor to None (D9)
    actor = actor or None

    # Verify node exists
    from taskyn.graph.nodes import get_node
    node = get_node(node_id)
    if node is None:
        raise NotFoundError("node", node_id)
    node_id = node.id  # Use full ID

    # Enforce can_track_time
    _enforce_time_tracking(node)

    entry_id = uuid4().hex
    now = _now()

    execute(
        """
        INSERT INTO time_entries (id, node_id, started_at, ended_at, duration_minutes, notes, source, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (entry_id, node_id, now, now, duration_minutes, notes, source, actor, now),
    )

    log_activity(
        entity_type="time_entry",
        entity_id=entry_id,
        action="time_logged",
        new_value=str(duration_minutes),
        node_type=node.node_type,
        actor=actor,
    )

    commit()

    propagate_actual_time(node_id)

    return TimeEntry(
        id=entry_id,
        node_id=node_id,
        started_at=now,
        ended_at=now,
        duration_minutes=duration_minutes,
        notes=notes,
        source=source,
        actor=actor,
        created_at=now,
    )


def get_active_timer(actor: str | None = None) -> TimeEntry | None:
    """Get the active timer for a specific actor."""
    row = fetchone(
        "SELECT * FROM time_entries WHERE actor IS ? AND ended_at IS NULL "
        "ORDER BY started_at DESC LIMIT 1",
        (actor,),
    )
    if row is None:
        return None
    return _row_to_time_entry(row)


def get_active_timers() -> list[TimeEntry]:
    """Get all active timers across all actors."""
    rows = fetchall(
        "SELECT * FROM time_entries WHERE ended_at IS NULL ORDER BY started_at DESC"
    )
    return [_row_to_time_entry(row) for row in rows]


def list_time_entries(node_id: str) -> list[TimeEntry]:
    """List all time entries for a node (supports prefix matching)."""
    from taskyn.graph.nodes import get_node
    node = get_node(node_id)
    if node is None:
        return []
    node_id = node.id  # Use full ID

    rows = fetchall(
        "SELECT * FROM time_entries WHERE node_id = ? ORDER BY started_at DESC",
        (node_id,),
    )
    return [_row_to_time_entry(row) for row in rows]


def list_all_time_entries(
    project_id: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """List time entries across all nodes, with node title attached.

    Args:
        project_id: Optional filter by project.
        limit: Max entries to return (default 200).

    Returns:
        List of dicts: time entry fields + node_title.
    """
    if project_id:
        rows = fetchall(
            """
            SELECT te.*, n.title AS node_title
            FROM time_entries te
            JOIN nodes n ON te.node_id = n.id
            WHERE n.project_id = ?
            ORDER BY te.started_at DESC
            LIMIT ?
            """,
            (project_id, limit),
        )
    else:
        rows = fetchall(
            """
            SELECT te.*, n.title AS node_title
            FROM time_entries te
            JOIN nodes n ON te.node_id = n.id
            ORDER BY te.started_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    result = []
    for row in rows:
        entry = _row_to_time_entry(row)
        d = entry.model_dump()
        d["node_title"] = row["node_title"]
        result.append(d)
    return result


def get_time_total(node_id: str) -> int:
    """Get total time tracked on a node in minutes (supports prefix matching)."""
    from taskyn.graph.nodes import get_node
    node = get_node(node_id)
    if node is None:
        return 0
    node_id = node.id  # Use full ID

    row = fetchone(
        "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM time_entries WHERE node_id = ?",
        (node_id,),
    )
    return row["total"] if row else 0


def _get_time_entry(entry_id: str) -> TimeEntry | None:
    """Get a time entry by ID."""
    row = fetchone("SELECT * FROM time_entries WHERE id = ?", (entry_id,))
    if row is None:
        return None
    return _row_to_time_entry(row)


def _get_active_timer_for_node(
    node_id: str,
    actor: str | None = None,
) -> TimeEntry | None:
    """Get the active timer for a specific node and actor (supports prefix matching)."""
    from taskyn.graph.nodes import get_node
    node = get_node(node_id)
    if node is None:
        return None
    node_id = node.id  # Use full ID

    row = fetchone(
        "SELECT * FROM time_entries WHERE node_id = ? AND actor IS ? "
        "AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
        (node_id, actor),
    )
    if row is None:
        return None
    return _row_to_time_entry(row)


def _row_to_time_entry(row) -> TimeEntry:
    """Convert a database row to a TimeEntry model."""
    return TimeEntry(
        id=row["id"],
        node_id=row["node_id"],
        started_at=_parse_datetime(row["started_at"]),
        ended_at=_parse_datetime(row["ended_at"]) if row["ended_at"] else None,
        duration_minutes=row["duration_minutes"],
        notes=row["notes"],
        source=row["source"],
        actor=row["actor"],
        created_at=_parse_datetime(row["created_at"]),
    )


def delete_time_entry(entry_id: str, actor: str | None = None) -> bool:
    """Delete a time entry by ID."""
    entry = _get_time_entry(entry_id)
    if entry is None:
        return False

    node_id = entry.node_id

    log_activity(
        entity_type="time_entry",
        entity_id=entry_id,
        action="deleted",
        old_value=str(entry.duration_minutes) if entry.duration_minutes else "running",
        actor=actor,
    )

    execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))
    commit()

    propagate_actual_time(node_id)

    return True


def get_time_entry(entry_id: str) -> TimeEntry | None:
    """Get a time entry by ID (public API)."""
    return _get_time_entry(entry_id)


def propagate_actual_time(node_id: str) -> None:
    """Recalculate actual_time for a node and propagate up the parent chain.

    - Leaf node: actual_time = sum of own time entries (in seconds)
    - Parent node: actual_time = own entries time + sum of children's actual_time
    - Walks up parent edges recursively until root
    """
    from taskyn.graph.nodes import get_node
    from taskyn.graph.edges import list_edges

    node = get_node(node_id)
    if node is None:
        return

    node_id = node.id

    # Calculate own time from completed time entries (seconds precision)
    # For timed entries: use started_at/ended_at timestamps
    # For manual entries (started_at == ended_at): use duration_minutes * 60
    row = fetchone(
        """
        SELECT COALESCE(SUM(
            CASE
                WHEN started_at = ended_at THEN duration_minutes * 60
                WHEN ended_at IS NOT NULL THEN CAST((julianday(ended_at) - julianday(started_at)) * 86400 AS INTEGER)
                ELSE 0
            END
        ), 0) as total
        FROM time_entries WHERE node_id = ? AND ended_at IS NOT NULL
        """,
        (node_id,),
    )
    own_time = row["total"] if row else 0

    # Sum children's actual_time (children have parent edge: source=child, target=this node)
    children_row = fetchone(
        """
        SELECT COALESCE(SUM(n.actual_time), 0) as total
        FROM nodes n
        JOIN edges e ON e.source_id = n.id
        WHERE e.target_id = ? AND e.edge_type = 'parent'
        """,
        (node_id,),
    )
    children_time = children_row["total"] if children_row else 0

    new_actual_time = own_time + children_time

    execute(
        "UPDATE nodes SET actual_time = ?, updated_at = ? WHERE id = ?",
        (new_actual_time, _now(), node_id),
    )
    commit()

    # Walk up: find this node's parent
    parent_edges = list_edges(source_id=node_id, edge_type="parent")
    for edge in parent_edges:
        propagate_actual_time(edge.target_id)


def _parse_datetime(value) -> datetime:
    """Parse a datetime from SQLite."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return _now()
