"""Node request schemas."""

from pydantic import BaseModel, Field


class NodeCreate(BaseModel):
    """Create node request."""
    project_id: str = Field(max_length=64)
    node_type: str = Field(max_length=64)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    assignee: str | None = Field(default=None, max_length=255)
    priority: str | None = Field(default=None, max_length=32)
    milestone_id: str | None = Field(default=None, max_length=64)
    parent_id: str | None = Field(default=None, max_length=64)


class NodeUpdate(BaseModel):
    """Update node request."""
    title: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = Field(default=None, max_length=64)
    assignee: str | None = Field(default=None, max_length=255)
    priority: str | None = Field(default=None, max_length=32)
    milestone_id: str | None = Field(default=None, max_length=64)


class BlockRequest(BaseModel):
    """Block node request."""
    reason: str = Field(min_length=1, max_length=1000)


class TagRequest(BaseModel):
    """Tag node request."""
    tag_name: str = Field(min_length=1, max_length=100)
