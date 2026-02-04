"""JWT token creation and decoding."""

import os
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

_MIN_SECRET_LENGTH = 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _load_secret() -> str:
    """Load and validate the JWT secret from environment."""
    secret = os.getenv("TASKYN_JWT_SECRET", "")
    if not secret:
        raise RuntimeError(
            "TASKYN_JWT_SECRET environment variable is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    if len(secret) < _MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"TASKYN_JWT_SECRET must be at least {_MIN_SECRET_LENGTH} characters "
            f"(got {len(secret)}). Use a cryptographically random value."
        )
    return secret


SECRET_KEY = _load_secret()


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
