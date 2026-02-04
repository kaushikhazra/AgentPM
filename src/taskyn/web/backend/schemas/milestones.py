"""Milestone request schemas."""

from datetime import date

from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    """Create milestone request."""
    project_id: str = Field(max_length=64)
    name: str = Field(min_length=1, max_length=255)
    target_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)
