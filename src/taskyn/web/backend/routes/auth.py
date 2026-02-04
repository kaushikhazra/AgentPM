"""Auth routes — register, login, logout, refresh, me."""

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..auth.jwt import create_access_token, create_refresh_token, decode_token
from ..auth.password import hash_password, verify_password
from ..auth.users import User, create_user, get_user, get_user_by_email
from ..deps import get_current_user
from ..schemas.auth import MessageResponse, TokenResponse, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])
_rate_limit_enabled = os.getenv("TASKYN_RATE_LIMIT", "true").lower() != "false"
limiter = Limiter(key_func=get_remote_address, enabled=_rate_limit_enabled)

_COOKIE_SECURE = os.getenv("TASKYN_COOKIE_SECURE", "false").lower() == "true"
_COOKIE_ATTRS = dict(
    key="refresh_token",
    httponly=True,
    secure=_COOKIE_SECURE,
    samesite="lax",
    path="/",
)


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, data: UserCreate):
    """Create a new user account."""
    if get_user_by_email(data.email):
        raise HTTPException(409, detail="Registration failed")

    user = create_user(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    return MessageResponse(message="Account created", user_id=user.id)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: UserLogin, response: Response):
    """Login and receive an access token. Refresh token set as HTTP-only cookie."""
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, detail="Invalid credentials")

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        **_COOKIE_ATTRS,
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return TokenResponse(accessToken=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Logout by clearing the refresh cookie."""
    response.delete_cookie(**_COOKIE_ATTRS)
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh(request: Request):
    """Get a new access token using the refresh cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, detail="No refresh token")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, detail="Invalid token type")

        user_id = payload["sub"]
        user = get_user(user_id)
        if not user:
            raise HTTPException(401, detail="User not found")

        access_token = create_access_token(user.id, user.email)
        return TokenResponse(accessToken=access_token)

    except JWTError:
        raise HTTPException(401, detail="Invalid or expired refresh token")


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    """Get the current user's info."""
    return current_user
