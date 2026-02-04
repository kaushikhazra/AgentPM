"""Auth routes — register, login, logout, refresh, me."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import JWTError

from ..auth.jwt import create_access_token, create_refresh_token, decode_token
from ..auth.password import hash_password, verify_password
from ..auth.users import User, create_user, get_user, get_user_by_email
from ..deps import get_current_user
from ..schemas.auth import MessageResponse, TokenResponse, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(data: UserCreate):
    """Create a new user account."""
    if get_user_by_email(data.email):
        raise HTTPException(409, detail="Email already registered")

    user = create_user(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )
    return MessageResponse(message="Account created", user_id=user.id)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, response: Response):
    """Login and receive an access token. Refresh token set as HTTP-only cookie."""
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, detail="Invalid credentials")

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # False for local dev; True in production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return TokenResponse(accessToken=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Logout by clearing the refresh cookie."""
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=TokenResponse)
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
