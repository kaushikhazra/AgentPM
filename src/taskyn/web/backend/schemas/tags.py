"""Tag request schemas."""

from pydantic import BaseModel


class TagCreate(BaseModel):
    """Create tag request."""
    name: str
    color: str | None = None
