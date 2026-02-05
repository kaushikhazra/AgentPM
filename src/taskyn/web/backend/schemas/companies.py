"""Company request schemas."""

from pydantic import BaseModel, Field

from taskyn.db.enums import EntityType


class CompanyCreate(BaseModel):
    """Create company request."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    type: EntityType = Field(default=EntityType.DISCOVERY)


class CompanyUpdate(BaseModel):
    """Update company request."""
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    type: EntityType | None = Field(default=None)
