import logging
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.routes import (
    assignments,
    audit,
    auth,
    certificates,
    completions,
    courses,
    dashboard,
    employees,
    learning_tracks,
)
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.http import BodySizeLimitMiddleware

settings = get_settings()
app = FastAPI(
    title="Learning Tracker",
    version="1.0.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.add_middleware(
    BodySizeLimitMiddleware, max_bytes=settings.max_upload_bytes + 1024 * 1024
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    request.state.request_id = str(uuid4())
    content_length = request.headers.get("content-length")
    try:
        too_large = (
            content_length
            and int(content_length) > settings.max_upload_bytes + 1024 * 1024
        )
    except ValueError:
        too_large = True
    if too_large:
        response = JSONResponse(
            {
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "Request body is too large",
                    "request_id": request.state.request_id,
                }
            },
            status_code=413,
        )
    else:
        response = await call_next(request)
    response.headers.update(
        {
            "X-Request-ID": request.state.request_id,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "same-origin",
            "Cache-Control": "no-store",
        }
    )
    if settings.cookie_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


def error_response(request, status, code, message, details=None):
    return JSONResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
        status_code=status,
    )


@app.exception_handler(AppError)
async def application_error(request, exc):
    return error_response(request, exc.status, exc.code, exc.message)


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return error_response(request, exc.status_code, "HTTP_ERROR", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo submitted credentials or file contents in errors.
    fields = [
        {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return error_response(
        request, 422, "VALIDATION_ERROR", "Check the supplied information", fields
    )


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return error_response(
        request,
        409,
        "DATA_CONFLICT",
        "A unique value already exists or this change conflicts with a related record",
    )


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logging.getLogger(__name__).error(
        "Request %s failed (%s)", request.state.request_id, type(exc).__name__
    )
    return error_response(
        request, 500, "INTERNAL_ERROR", "An unexpected error occurred"
    )


for router in (
    auth.router,
    employees.router,
    courses.router,
    learning_tracks.router,
    assignments.router,
    assignments.my_router,
    completions.router,
    certificates.router,
    dashboard.router,
    audit.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/api/health")
def health():
    return {"status": "ok"}
