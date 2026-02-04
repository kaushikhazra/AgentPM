"""Company request schemas."""

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    """Create company request."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
