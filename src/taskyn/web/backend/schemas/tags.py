"""Tag request schemas."""

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """Create tag request."""
    name: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=20)
