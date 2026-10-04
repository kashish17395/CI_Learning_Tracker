from fastapi import APIRouter, Depends
from app.db.session import get_db
from app.dependencies.auth import identity
from app.schemas.requests import ProgressPatch
from app.services import learning

router = APIRouter(prefix="/completions", tags=["Progress and completion"])


@router.get("/{attempt_id}")
def detail(attempt_id: str, current=Depends(identity), db=Depends(get_db)):
    return learning.attempt_view(
        db, learning.permitted_attempt(db, current.user, attempt_id)
    )


@router.patch("/{attempt_id}")
def update(
    attempt_id: str,
    payload: ProgressPatch,
    current=Depends(identity),
    db=Depends(get_db),
):
    return learning.update_progress(db, current.user, attempt_id, payload)
