"""Milestone CRUD operations."""

from datetime import datetime, date, timezone
from uuid import uuid4

from agentpm.db.connection import execute, fetchone, fetchall, commit
from agentpm.db.models import Milestone
from agentpm.core.activity import log_activity
from agentpm.core.project import get_project
from agentpm.exceptions import NotFoundError, ValidationError


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def create_milestone(
    project_id: str,
    name: str,
    description: str | None = None,
    target_date: date | None = None,
    actor: str | None = None,
) -> Milestone:
    """Create a new milestone."""
    # Validate project exists (supports prefix matching)
    project = get_project(project_id)
    if project is None:
        raise NotFoundError("project", project_id)
    project_id = project.id  # Use full ID

    milestone_id = uuid4().hex
    now = _now()

    execute(
        """
        INSERT INTO milestones (id, project_id, name, description, target_date, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (milestone_id, project_id, name, description, target_date, "open", now, now),
    )

    log_activity(
        entity_type="milestone",
        entity_id=milestone_id,
        action="created",
        new_value=name,
        actor=actor,
    )

    commit()

    return Milestone(
        id=milestone_id,
        project_id=project_id,
        name=name,
        description=description,
        target_date=target_date,
        status="open",
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


def get_milestone(milestone_id: str) -> Milestone | None:
    """Get a milestone by ID."""
    row = fetchone("SELECT * FROM milestones WHERE id = ?", (milestone_id,))
    if row is None:
        return None
    return _row_to_milestone(row)


def list_milestones(
    project_id: str,
    status: str | None = None,
) -> list[Milestone]:
    """List milestones for a project (supports prefix matching)."""
    # Resolve project ID prefix
    project = get_project(project_id)
    if project is None:
        return []
    project_id = project.id

    sql = "SELECT * FROM milestones WHERE project_id = ?"
    params = [project_id]

    if status is not None:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY target_date, name"

    rows = fetchall(sql, tuple(params))
    return [_row_to_milestone(row) for row in rows]


def update_milestone(
    milestone_id: str,
    name: str | None = None,
    description: str | None = None,
    target_date: date | None = None,
    actor: str | None = None,
) -> Milestone:
    """Update a milestone."""
    milestone = get_milestone(milestone_id)
    if milestone is None:
        raise NotFoundError("milestone", milestone_id)

    now = _now()
    updates = []
    params = []

    if name is not None and name != milestone.name:
        updates.append("name = ?")
        params.append(name)

    if description is not None and description != milestone.description:
        updates.append("description = ?")
        params.append(description)

    if target_date is not None and target_date != milestone.target_date:
        updates.append("target_date = ?")
        params.append(target_date)

    if not updates:
        return milestone

    updates.append("updated_at = ?")
    params.append(now)
    params.append(milestone_id)

    execute(
        f"UPDATE milestones SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    commit()

    return get_milestone(milestone_id)


def complete_milestone(milestone_id: str, actor: str | None = None) -> Milestone:
    """Mark a milestone as completed."""
    milestone = get_milestone(milestone_id)
    if milestone is None:
        raise NotFoundError("milestone", milestone_id)

    if milestone.status == "completed":
        return milestone

    now = _now()

    execute(
        "UPDATE milestones SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
        ("completed", now, now, milestone_id),
    )

    log_activity(
        entity_type="milestone",
        entity_id=milestone_id,
        action="completed",
        old_value="open",
        new_value="completed",
        actor=actor,
    )

    commit()

    return get_milestone(milestone_id)


def delete_milestone(milestone_id: str, actor: str | None = None) -> bool:
    """Delete a milestone."""
    milestone = get_milestone(milestone_id)
    if milestone is None:
        return False

    log_activity(
        entity_type="milestone",
        entity_id=milestone_id,
        action="deleted",
        old_value=milestone.name,
        actor=actor,
    )

    execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
    commit()

    return True


def _row_to_milestone(row) -> Milestone:
    """Convert a database row to a Milestone model."""
    return Milestone(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"],
        target_date=_parse_date(row["target_date"]) if row["target_date"] else None,
        status=row["status"],
        completed_at=_parse_datetime(row["completed_at"]) if row["completed_at"] else None,
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def _parse_date(value) -> date | None:
    """Parse a date from SQLite."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return None


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
