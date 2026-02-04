"""Project request schemas."""

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    """Create project request."""
    company_id: str
    name: str
    methodology: str = "classic_agile"
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Update project request."""
    name: str | None = None
    description: str | None = None
    status: str | None = None
