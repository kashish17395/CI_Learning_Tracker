from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy import select
from app.api.params import paging
from app.core.config import get_settings
from app.db.session import get_db
from app.dependencies.auth import employee_for, identity, manager
from app.models import Certificate, Course, Employee, LearningAttempt
from app.repositories.catalog import page
from app.schemas.requests import RevokeCertificate
from app.services import certificates
from app.services.common import dump

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("")
def listing(
    employee_id: str | None = None,
    attempt_id: str | None = None,
    params=Depends(paging),
    current=Depends(identity),
    db=Depends(get_db),
):
    query = select(LearningAttempt.id)
    if current.user.role != "MANAGER":
        employee = employee_for(db, current.user)
        query = query.where(
            LearningAttempt.employee_id == (employee.id if employee else "__none__")
        )
    elif employee_id:
        query = query.where(LearningAttempt.employee_id == employee_id)
    filters = [
        Certificate.learning_attempt_id.in_(query),
        Certificate.revoked_at.is_(None),
    ]
    if attempt_id:
        filters.append(Certificate.learning_attempt_id == attempt_id)
    rows, total = page(
        db,
        Certificate,
        fields=("original_filename",),
        filters=filters,
        allowed_sort=("created_at", "original_filename", "uploaded_at"),
        **params
    )
    items = []
    for cert in rows:
        attempt = db.get(LearningAttempt, cert.learning_attempt_id)
        items.append(
            {
                **dump(cert, exclude=("blob_key",)),
                "employee_name": db.get(Employee, attempt.employee_id).name,
                "course_name": db.get(Course, attempt.course_id).name,
            }
        )
    return {
        "items": items,
        "total": total,
        "page": params["page"],
        "page_size": params["page_size"],
    }


@router.post("", status_code=201)
def upload(
    attempt_id: str = Form(...),
    file: UploadFile = File(...),
    current=Depends(identity),
    db=Depends(get_db),
):
    # Reading is bounded; reverse proxy additionally caps the full multipart body.
    data = file.file.read(get_settings().max_upload_bytes + 1)
    return certificates.upload(
        db, current.user, attempt_id, file.filename, file.content_type, data
    )


@router.get("/{id}/download")
def download(id: str, current=Depends(identity), db=Depends(get_db)):
    cert, data = certificates.download(db, current.user, id)
    return Response(
        data,
        media_type=cert.content_type,
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''"
            + quote(cert.original_filename, safe=""),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/{id}/revoke")
def revoke(
    id: str, payload: RevokeCertificate, current=Depends(manager), db=Depends(get_db)
):
    return certificates.revoke(db, current.user, id, payload.reason)
