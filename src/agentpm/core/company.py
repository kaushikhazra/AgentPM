"""Company CRUD operations."""

import json
from datetime import datetime
from uuid import uuid4

from agentpm.db.connection import execute, fetchone, fetchall, commit
from agentpm.db.models import Company
from agentpm.exceptions import ValidationError


def create_company(
    name: str,
    description: str | None = None,
    actor: str | None = None,
) -> Company:
    """Create a new company."""
    # Check for duplicate company name
    existing = fetchone("SELECT id FROM companies WHERE name = ?", (name,))
    if existing:
        raise ValidationError(f"Company '{name}' already exists")

    company_id = uuid4().hex
    now = datetime.utcnow()

    execute(
        """
        INSERT INTO companies (id, name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (company_id, name, description, now, now),
    )

    # Log activity
    execute(
        """
        INSERT INTO activity_log (id, entity_type, entity_id, action, new_value, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (uuid4().hex, "company", company_id, "created", name, actor, now),
    )

    commit()

    return Company(
        id=company_id,
        name=name,
        description=description,
        created_at=now,
        updated_at=now,
    )


def get_company(company_id: str) -> Company | None:
    """Get a company by ID (supports prefix matching)."""
    # Try exact match first
    row = fetchone(
        "SELECT * FROM companies WHERE id = ?",
        (company_id,),
    )

    # If not found, try prefix match
    if row is None and len(company_id) >= 4:
        rows = fetchall(
            "SELECT * FROM companies WHERE id LIKE ?",
            (company_id + "%",),
        )
        if len(rows) == 1:
            row = rows[0]
        elif len(rows) > 1:
            # Ambiguous prefix - return None to trigger "not found"
            return None

    if row is None:
        return None

    return _row_to_company(row)


def list_companies() -> list[Company]:
    """List all companies."""
    rows = fetchall("SELECT * FROM companies ORDER BY name")
    return [_row_to_company(row) for row in rows]


def update_company(
    company_id: str,
    name: str | None = None,
    description: str | None = None,
    actor: str | None = None,
) -> Company | None:
    """Update a company."""
    company = get_company(company_id)
    if company is None:
        return None

    now = datetime.utcnow()
    updates = []
    params = []

    if name is not None and name != company.name:
        updates.append("name = ?")
        params.append(name)
        # Log activity
        execute(
            """
            INSERT INTO activity_log (id, entity_type, entity_id, action, old_value, new_value, actor, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (uuid4().hex, "company", company_id, "updated", company.name, name, actor, now),
        )

    if description is not None and description != company.description:
        updates.append("description = ?")
        params.append(description)

    if not updates:
        return company

    updates.append("updated_at = ?")
    params.append(now)
    params.append(company_id)

    execute(
        f"UPDATE companies SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    commit()

    return get_company(company_id)


def delete_company(company_id: str, actor: str | None = None) -> bool:
    """Delete a company."""
    company = get_company(company_id)
    if company is None:
        return False

    now = datetime.utcnow()

    # Log activity
    execute(
        """
        INSERT INTO activity_log (id, entity_type, entity_id, action, old_value, actor, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (uuid4().hex, "company", company_id, "deleted", company.name, actor, now),
    )

    execute("DELETE FROM companies WHERE id = ?", (company_id,))
    commit()

    return True


def _row_to_company(row) -> Company:
    """Convert a database row to a Company model."""
    return Company(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def _parse_datetime(value) -> datetime:
    """Parse a datetime from SQLite."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Handle various formats
        for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.utcnow()
