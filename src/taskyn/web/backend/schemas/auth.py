"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Access token response."""
    accessToken: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    user_id: str | None = None
