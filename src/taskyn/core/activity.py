"""Activity logging for Taskyn."""

from datetime import datetime, timezone
from uuid import uuid4

from taskyn.db.connection import execute, fetchone, fetchall, commit
from taskyn.db.models import ActivityLog


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def log_activity(
    entity_type: str,
    entity_id: str,
    action: str,
    old_value: str | None = None,
    new_value: str | None = None,
    node_type: str | None = None,
    actor: str | None = None,
    notes: str | None = None,
) -> ActivityLog:
    """Log an activity entry."""
    activity_id = uuid4().hex
    now = _now()

    execute(
        """
        INSERT INTO activity_log (id, entity_type, entity_id, node_type, action, old_value, new_value, actor, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (activity_id, entity_type, entity_id, node_type, action, old_value, new_value, actor, notes, now),
    )
    commit()

    return ActivityLog(
        id=activity_id,
        entity_type=entity_type,
        entity_id=entity_id,
        node_type=node_type,
        action=action,
        old_value=old_value,
        new_value=new_value,
        actor=actor,
        notes=notes,
        created_at=now,
    )


def list_activity(
    entity_type: str | None = None,
    entity_id: str | None = None,
    node_type: str | None = None,
    actor: str | None = None,
    limit: int = 50,
) -> list[ActivityLog]:
    """List activity entries with optional filters."""
    sql = "SELECT * FROM activity_log WHERE 1=1"
    params = []

    if entity_type is not None:
        sql += " AND entity_type = ?"
        params.append(entity_type)

    if entity_id is not None:
        sql += " AND entity_id = ?"
        params.append(entity_id)

    if node_type is not None:
        sql += " AND node_type = ?"
        params.append(node_type)

    if actor is not None:
        sql += " AND actor = ?"
        params.append(actor)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = fetchall(sql, tuple(params))
    return [_row_to_activity(row) for row in rows]


def get_entity_activity(entity_type: str, entity_id: str, limit: int = 50) -> list[ActivityLog]:
    """Get activity for a specific entity."""
    return list_activity(entity_type=entity_type, entity_id=entity_id, limit=limit)


def _row_to_activity(row) -> ActivityLog:
    """Convert a database row to an ActivityLog model."""
    return ActivityLog(
        id=row["id"],
        entity_type=row["entity_type"],
        entity_id=row["entity_id"],
        node_type=row["node_type"],
        action=row["action"],
        old_value=row["old_value"],
        new_value=row["new_value"],
        actor=row["actor"],
        notes=row["notes"],
        created_at=_parse_datetime(row["created_at"]),
    )


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
