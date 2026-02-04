"""Timer and time entry request schemas."""

from pydantic import BaseModel


class TimerStart(BaseModel):
    """Start timer request."""
    node_id: str
    notes: str | None = None


class TimerStop(BaseModel):
    """Stop timer request."""
    entry_id: str | None = None


class TimeEntryCreate(BaseModel):
    """Log time entry request."""
    node_id: str
    duration_minutes: int
    notes: str | None = None
