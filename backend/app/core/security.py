import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from app.core.config import get_settings

hasher = PasswordHasher()
# Comparable verification work for unknown identities.
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))


def now():
    return datetime.now(timezone.utc)


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def random_token() -> str:
    return secrets.token_urlsafe(48)


def access_token(user, session_id: str) -> str:
    settings = get_settings()
    return jwt.encode(
        {
            "sub": user.id,
            "role": user.role,
            "sid": session_id,
            "iat": now(),
            "exp": now() + timedelta(minutes=settings.access_minutes),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
