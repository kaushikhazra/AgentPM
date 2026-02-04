"""Edge request schemas."""

from pydantic import BaseModel, Field


class EdgeCreate(BaseModel):
    """Create edge request."""
    source_id: str = Field(max_length=64)
    target_id: str = Field(max_length=64)
    edge_type: str = Field(max_length=64)
