from dataclasses import dataclass
from secrets import compare_digest
from fastapi import Depends, Request
import jwt
from app.core.config import get_settings
from app.core.errors import AppError, missing
from app.core.security import digest, now, utc
from app.db.session import get_db
from app.models import AuthSession, Employee, User
from sqlalchemy import select


@dataclass
class Identity:
    user: User
    session: AuthSession


def check_origin(request):
    if request.headers.get("origin") != get_settings().public_origin:
        raise AppError(403, "ORIGIN_FAILED", "Request origin not permitted")


def identity(request: Request, db=Depends(get_db)):
    try:
        claims = jwt.decode(
            request.cookies.get("lt_access", ""),
            get_settings().jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "role", "sid", "iat", "exp"]},
        )
        user = db.get(User, claims["sub"])
        session = db.get(AuthSession, claims["sid"])
        if (
            not user
            or not user.is_active
            or not session
            or session.user_id != user.id
            or session.revoked_at
            or utc(session.expires_at) <= now()
        ):
            raise ValueError()
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise AppError(401, "UNAUTHENTICATED", "Please sign in")
    db.info["request_id"] = request.state.request_id
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        check_origin(request)
        csrf = request.headers.get("x-csrf-token", "")
        if not csrf or not compare_digest(digest(csrf), session.csrf_hash):
            raise AppError(403, "CSRF_FAILED", "Invalid security token")
    return Identity(user, session)


def manager(current=Depends(identity)):
    if current.user.role != "MANAGER":
        raise AppError(403, "FORBIDDEN", "Manager access required")
    return current


def own_employee(db, user, employee_id):
    employee = db.get(Employee, employee_id)
    if not employee or (user.role != "MANAGER" and employee.user_id != user.id):
        missing()
    return employee


def employee_for(db, user):
    return db.scalar(select(Employee).where(Employee.user_id == user.id))
