"""Common response schemas."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str | None = None
    code: str | None = None
