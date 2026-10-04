from datetime import timedelta
from secrets import compare_digest
from sqlalchemy import select
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    DUMMY_HASH,
    access_token,
    digest,
    hash_password,
    hasher,
    now,
    random_token,
    utc,
    verify_password,
)
from app.models import AuthSession, Employee, RefreshToken, User


def user_view(db, user):
    employee = db.scalar(select(Employee).where(Employee.user_id == user.id))
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "name": employee.name if employee else user.email.split("@")[0],
        "employee_id": employee.id if employee else None,
    }


def login(db, email, password):
    user = db.scalar(select(User).where(User.email == email.lower()))
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise AppError(401, "INVALID_CREDENTIALS", "Invalid email or password")
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    csrf, raw = random_token(), random_token()
    session = AuthSession(
        user_id=user.id,
        csrf_hash=digest(csrf),
        expires_at=now() + timedelta(days=get_settings().refresh_days),
    )
    db.add(session)
    db.flush()
    db.add(
        RefreshToken(
            session_id=session.id, token_hash=digest(raw), expires_at=session.expires_at
        )
    )
    db.commit()
    return user_view(db, user), access_token(user, session.id), raw, csrf


def refresh(db, raw, csrf):
    token = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == digest(raw or ""))
        .with_for_update()
    )
    if not token:
        raise AppError(401, "INVALID_SESSION", "Please sign in again")
    session = db.scalar(
        select(AuthSession).where(AuthSession.id == token.session_id).with_for_update()
    )
    if not csrf or not compare_digest(digest(csrf), session.csrf_hash):
        raise AppError(403, "CSRF_FAILED", "Invalid security token")
    if token.consumed_at:
        session.revoked_at = now()
        db.commit()
        raise AppError(401, "TOKEN_REUSE", "Session revoked; please sign in again")
    user = db.get(User, session.user_id)
    if (
        session.revoked_at
        or utc(session.expires_at) <= now()
        or utc(token.expires_at) <= now()
        or not user.is_active
    ):
        raise AppError(401, "INVALID_SESSION", "Please sign in again")
    raw_next = random_token()
    token.consumed_at = now()
    replacement = RefreshToken(
        session_id=session.id,
        token_hash=digest(raw_next),
        expires_at=session.expires_at,
    )
    db.add(replacement)
    db.flush()
    token.replaced_by_id = replacement.id
    db.commit()
    return access_token(user, session.id), raw_next, session.expires_at


def logout(db, session):
    session.revoked_at = now()
    db.commit()
