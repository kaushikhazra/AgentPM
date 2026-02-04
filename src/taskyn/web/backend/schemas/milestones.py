"""Milestone request schemas."""

from pydantic import BaseModel


class MilestoneCreate(BaseModel):
    """Create milestone request."""
    project_id: str
    name: str
    target_date: str | None = None
    description: str | None = None
