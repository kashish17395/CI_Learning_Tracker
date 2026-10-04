import hashlib
import io
import logging
import warnings
from pathlib import PurePath
from uuid import uuid4
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from app.core.config import get_settings
from app.core.errors import AppError, invalid, missing
from app.core.security import now
from app.models import Certificate, Employee
from app.repositories.catalog import get
from app.services.common import audit, dump
from app.services.learning import active_contexts, permitted_attempt
from app.storage.service import storage

logger = logging.getLogger(__name__)
ALLOWED = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def validate_file(filename, content_type, data):
    name = (filename or "").replace("\\", "/").split("/")[-1]
    extension = PurePath(name).suffix.lower()
    if extension not in ALLOWED or ALLOWED[extension] != content_type:
        invalid("Upload a PDF, PNG or JPEG with a matching content type")
    if not data:
        invalid("File is empty")
    if len(data) > get_settings().max_upload_bytes:
        raise AppError(413, "FILE_TOO_LARGE", "Maximum file size is 10 MiB")
    if extension == ".pdf":
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
            invalid("Invalid PDF signature")
    else:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as image:
                    if image.format != ("PNG" if extension == ".png" else "JPEG"):
                        invalid("File contents do not match the extension")
                    image.verify()
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            invalid("Invalid or excessively large image")
    return name[:255], extension


def upload(db, actor, attempt_id, filename, content_type, data):
    attempt = permitted_attempt(db, actor, attempt_id)
    get(db, Employee, attempt.employee_id, lock=True)
    contexts = active_contexts(db, attempt.id)
    if not contexts or attempt.retired_at:
        invalid("No active assignment permits uploads")
    if actor.role == "EMPLOYEE" and not all(a.employee_can_update for _, a in contexts):
        raise AppError(403, "EVIDENCE_LOCKED", "Evidence is managed by your manager")
    name, extension = validate_file(filename, content_type, data)
    key = f"certificates/{attempt.employee_id}/{attempt.id}/{uuid4()}{extension}"
    store = storage()
    store.upload(key, data, content_type)
    cert = Certificate(
        learning_attempt_id=attempt.id,
        original_filename=name,
        blob_key=key,
        content_type=content_type,
        file_size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        uploaded_by=actor.id,
    )
    try:
        db.add(cert)
        db.flush()
        audit(
            db,
            actor,
            "CERTIFICATE_UPLOADED",
            cert,
            {"attempt_id": attempt.id, "file_size": len(data)},
        )
        db.commit()
    except Exception:
        db.rollback()
        try:
            store.delete(key)
        except Exception:
            logger.exception("Object cleanup failed for certificate object %s", key)
        raise
    return dump(cert, exclude=("blob_key",))


def authorized_certificate(db, actor, id):
    cert = get(db, Certificate, id)
    permitted_attempt(db, actor, cert.learning_attempt_id)
    return cert


def download(db, actor, id):
    cert = authorized_certificate(db, actor, id)
    if cert.revoked_at:
        missing()
    data = storage().download(cert.blob_key)
    audit(db, actor, "CERTIFICATE_DOWNLOADED", cert)
    db.commit()
    return cert, data


def revoke(db, actor, id, reason):
    cert = authorized_certificate(db, actor, id)
    attempt = permitted_attempt(db, actor, cert.learning_attempt_id)
    get(db, Employee, attempt.employee_id, lock=True)
    if cert.revoked_at:
        invalid("Certificate already revoked")
    if attempt.status == "COMPLETED" and any(
        a.certificate_required for _, a in active_contexts(db, attempt.id)
    ):
        remaining = db.scalars(
            select(Certificate).where(
                Certificate.learning_attempt_id == attempt.id,
                Certificate.revoked_at.is_(None),
                Certificate.id != cert.id,
            )
        ).all()
        if not remaining:
            invalid(
                "Reopen the learning or upload replacement evidence before revoking its last required certificate"
            )
    cert.revoked_at, cert.revoked_by, cert.revocation_reason = now(), actor.id, reason
    audit(db, actor, "CERTIFICATE_REVOKED", cert, {"reason": reason})
    db.commit()
    return dump(cert, exclude=("blob_key",))
