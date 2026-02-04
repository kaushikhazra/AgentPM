"""Password hashing with bcrypt."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
