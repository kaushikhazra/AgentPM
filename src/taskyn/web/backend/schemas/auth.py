"""Auth request/response schemas."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Access token response."""
    accessToken: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    user_id: str | None = None
