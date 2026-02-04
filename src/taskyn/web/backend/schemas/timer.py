"""Timer and time entry request schemas."""

from pydantic import BaseModel, Field


class TimerStart(BaseModel):
    """Start timer request."""
    node_id: str = Field(max_length=64)
    notes: str | None = Field(default=None, max_length=1000)


class TimerStop(BaseModel):
    """Stop timer request."""
    entry_id: str | None = Field(default=None, max_length=64)


class TimeEntryCreate(BaseModel):
    """Log time entry request."""
    node_id: str = Field(max_length=64)
    duration_minutes: int = Field(gt=0, le=1440)
    notes: str | None = Field(default=None, max_length=1000)
