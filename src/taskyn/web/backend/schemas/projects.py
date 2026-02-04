"""Project request schemas."""

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Create project request."""
    company_id: str = Field(max_length=64)
    name: str = Field(min_length=1, max_length=255)
    methodology: str = Field(default="classic_agile", max_length=64)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    """Update project request."""
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, max_length=64)
