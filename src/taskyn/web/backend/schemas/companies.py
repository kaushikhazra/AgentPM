"""Company request schemas."""

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    """Create company request."""
    name: str
    description: str | None = None
