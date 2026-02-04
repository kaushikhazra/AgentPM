"""Node request schemas."""

from pydantic import BaseModel


class NodeCreate(BaseModel):
    """Create node request."""
    project_id: str
    node_type: str
    title: str
    description: str | None = None
    assignee: str | None = None
    priority: str | None = None
    milestone_id: str | None = None
    parent_id: str | None = None


class NodeUpdate(BaseModel):
    """Update node request."""
    title: str | None = None
    description: str | None = None
    status: str | None = None
    assignee: str | None = None
    priority: str | None = None
    milestone_id: str | None = None


class BlockRequest(BaseModel):
    """Block node request."""
    reason: str


class TagRequest(BaseModel):
    """Tag node request."""
    tag_name: str
