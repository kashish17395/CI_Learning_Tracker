from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response
from app.core.config import get_settings
from app.core.rate_limit import limit
from app.core.security import digest, now, utc
from app.db.session import get_db
from app.dependencies.auth import check_origin, identity
from app.schemas.requests import Login
from app.services import auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


def cookies(response, access, refresh, csrf=None, refresh_seconds=None):
    settings = get_settings()
    options = {"secure": settings.cookie_secure, "samesite": "lax", "path": "/"}
    response.set_cookie(
        "lt_access",
        access,
        httponly=True,
        max_age=settings.access_minutes * 60,
        **options
    )
    response.set_cookie(
        "lt_refresh",
        refresh,
        httponly=True,
        max_age=(
            refresh_seconds
            if refresh_seconds is not None
            else settings.refresh_days * 86400
        ),
        **options
    )
    if csrf:
        response.set_cookie(
            "lt_csrf",
            csrf,
            httponly=False,
            max_age=settings.refresh_days * 86400,
            **options
        )
    response.headers["Cache-Control"] = "no-store"


@router.post("/login")
def login(payload: Login, request: Request, response: Response, db=Depends(get_db)):
    check_origin(request)
    limit(
        "login:ip:" + (request.client.host if request.client else "unknown"), maximum=30
    )
    limit("login:email:" + digest(str(payload.email).lower()), maximum=10)
    user, access, refresh, csrf = auth.login(db, str(payload.email), payload.password)
    cookies(response, access, refresh, csrf)
    return user


@router.post("/refresh")
def refresh(request: Request, response: Response, db=Depends(get_db)):
    check_origin(request)
    limit(
        "refresh:" + (request.client.host if request.client else "unknown"), maximum=60
    )
    access, token, expires_at = auth.refresh(
        db, request.cookies.get("lt_refresh"), request.headers.get("x-csrf-token")
    )
    cookies(
        response,
        access,
        token,
        refresh_seconds=max(0, int((utc(expires_at) - now()).total_seconds())),
    )
    return {"message": "Session refreshed"}


@router.post("/logout", status_code=204)
def logout(response: Response, current=Depends(identity), db=Depends(get_db)):
    auth.logout(db, current.session)
    for name in ("lt_access", "lt_refresh", "lt_csrf"):
        response.delete_cookie(
            name, path="/", secure=get_settings().cookie_secure, samesite="lax"
        )


@router.get("/me")
def me(current=Depends(identity), db=Depends(get_db)):
    return auth.user_view(db, current.user)
