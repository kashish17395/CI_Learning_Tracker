from fastapi import APIRouter, Depends
from app.api.params import paging
from app.db.session import get_db
from app.dependencies.auth import identity, manager
from app.models import LearningTrack
from app.repositories.catalog import get, page
from app.schemas.requests import TrackCourses, TrackCreate, TrackPatch
from app.services import catalog

router = APIRouter(prefix="/learning-tracks", tags=["Learning tracks"])


@router.get("")
def listing(
    params=Depends(paging),
    active: bool | None = None,
    current=Depends(identity),
    db=Depends(get_db),
):
    rows, total = page(
        db,
        LearningTrack,
        fields=("name", "description"),
        filters=[LearningTrack.is_active == active] if active is not None else [],
        **params
    )
    return {
        "items": [catalog.track_view(db, t) for t in rows],
        "total": total,
        "page": params["page"],
        "page_size": params["page_size"],
    }


@router.post("", status_code=201)
def create(payload: TrackCreate, current=Depends(manager), db=Depends(get_db)):
    return catalog.create_track(db, current.user, payload)


@router.get("/{id}")
def detail(id: str, current=Depends(identity), db=Depends(get_db)):
    return catalog.track_view(db, get(db, LearningTrack, id))


@router.patch("/{id}")
def patch(id: str, payload: TrackPatch, current=Depends(manager), db=Depends(get_db)):
    return catalog.patch_track(db, current.user, id, payload)


@router.put("/{id}/courses")
def courses(
    id: str, payload: TrackCourses, current=Depends(manager), db=Depends(get_db)
):
    return catalog.update_track_courses(db, current.user, id, payload)
