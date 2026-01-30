"""Project CRUD operations."""

import json
from datetime import datetime
from uuid import uuid4

from agentpm.db.connection import execute, fetchone, fetchall, commit
from agentpm.db.models import Project
from agentpm.methodologies import methodology_exists
from agentpm.exceptions import ValidationError


def create_project(
    company_id: str,
    name: str,
    methodology: str = "classic_agile",
    description: str | None = None,
    config: dict | None = None,
    actor: str | None = None,
) -> Project:
    """Create a new project."""
    # Validate methodology exists
    if not methodology_exists(methodology):
        raise ValidationError(f"Unknown methodology: {methodology}")

    # Validate company exists
    company_row = fetchone("SELECT id FROM companies WHERE id = ?", (company_id,))
    if company_row is None:
        raise ValidationError(f"Company not found: {company_id}")

    project_id = uuid4().hex
    now = datetime.utcnow()
    config_json = json.dumps(config) if config else None

    execute(
        """
        INSERT INTO projects (id, company_id, name, description, methodology, status, config, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, company_id, name, description, methodology, "active", config_json, now, now),
    )

    # Log activity
    execute(
        """
        INSERT INTO activity_log (id, entity_type, entity_id, action, new_value, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (uuid4().hex, "project", project_id, "created", name, actor, now),
    )

    commit()

    return Project(
        id=project_id,
        company_id=company_id,
        name=name,
        description=description,
        methodology=methodology,
        status="active",
        config=config,
        created_at=now,
        updated_at=now,
    )


def get_project(project_id: str) -> Project | None:
    """Get a project by ID."""
    row = fetchone(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,),
    )

    if row is None:
        return None

    return _row_to_project(row)


def list_projects(
    company_id: str | None = None,
    status: str | None = None,
) -> list[Project]:
    """List projects with optional filters."""
    sql = "SELECT * FROM projects WHERE 1=1"
    params = []

    if company_id is not None:
        sql += " AND company_id = ?"
        params.append(company_id)

    if status is not None:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY name"

    rows = fetchall(sql, tuple(params))
    return [_row_to_project(row) for row in rows]


def update_project(
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    config: dict | None = None,
    actor: str | None = None,
) -> Project | None:
    """Update a project."""
    project = get_project(project_id)
    if project is None:
        return None

    # Validate status
    valid_statuses = ["active", "on_hold", "completed", "archived"]
    if status is not None and status not in valid_statuses:
        raise ValidationError(f"Invalid status: {status}. Must be one of: {valid_statuses}")

    now = datetime.utcnow()
    updates = []
    params = []

    if name is not None and name != project.name:
        updates.append("name = ?")
        params.append(name)

    if description is not None and description != project.description:
        updates.append("description = ?")
        params.append(description)

    if status is not None and status != project.status:
        updates.append("status = ?")
        params.append(status)
        # Log activity
        execute(
            """
            INSERT INTO activity_log (id, entity_type, entity_id, action, old_value, new_value, actor, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (uuid4().hex, "project", project_id, "status_changed", project.status, status, actor, now),
        )

    if config is not None:
        updates.append("config = ?")
        params.append(json.dumps(config))

    if not updates:
        return project

    updates.append("updated_at = ?")
    params.append(now)
    params.append(project_id)

    execute(
        f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    commit()

    return get_project(project_id)


def delete_project(project_id: str, actor: str | None = None) -> bool:
    """Delete a project."""
    project = get_project(project_id)
    if project is None:
        return False

    now = datetime.utcnow()

    # Log activity
    execute(
        """
        INSERT INTO activity_log (id, entity_type, entity_id, action, old_value, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (uuid4().hex, "project", project_id, "deleted", project.name, actor, now),
    )

    execute("DELETE FROM projects WHERE id = ?", (project_id,))
    commit()

    return True


def _row_to_project(row) -> Project:
    """Convert a database row to a Project model."""
    config = None
    if row["config"]:
        try:
            config = json.loads(row["config"])
        except json.JSONDecodeError:
            pass

    return Project(
        id=row["id"],
        company_id=row["company_id"],
        name=row["name"],
        description=row["description"],
        methodology=row["methodology"],
        status=row["status"],
        config=config,
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def _parse_datetime(value) -> datetime:
    """Parse a datetime from SQLite."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.utcnow()
