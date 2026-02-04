"""Edge request schemas."""

from pydantic import BaseModel


class EdgeCreate(BaseModel):
    """Create edge request."""
    source_id: str
    target_id: str
    edge_type: str
