"""JWT token creation and decoding."""

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY = os.getenv("TASKYN_JWT_SECRET", "taskyn-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
