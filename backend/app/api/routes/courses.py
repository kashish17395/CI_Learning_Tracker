from fastapi import APIRouter, Depends
from app.api.params import paging
from app.db.session import get_db
from app.dependencies.auth import identity, manager
from app.models import Course
from app.repositories.catalog import get, page
from app.schemas.requests import CourseCreate, CoursePatch
from app.services import catalog
from app.services.common import dump

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("")
def listing(
    params=Depends(paging),
    active: bool | None = None,
    category: str | None = None,
    current=Depends(identity),
    db=Depends(get_db),
):
    filters = []
    if active is not None:
        filters.append(Course.is_active == active)
    if category:
        filters.append(Course.category == category)
    rows, total = page(
        db,
        Course,
        fields=("name", "course_code", "category", "provider"),
        filters=filters,
        allowed_sort=("created_at", "name", "course_code", "category"),
        **params
    )
    return {
        "items": [dump(c) for c in rows],
        "total": total,
        "page": params["page"],
        "page_size": params["page_size"],
    }


@router.post("", status_code=201)
def create(payload: CourseCreate, current=Depends(manager), db=Depends(get_db)):
    return catalog.create_course(db, current.user, payload)


@router.get("/{id}")
def detail(id: str, current=Depends(identity), db=Depends(get_db)):
    return dump(get(db, Course, id))


@router.patch("/{id}")
def patch(id: str, payload: CoursePatch, current=Depends(manager), db=Depends(get_db)):
    return catalog.patch_course(db, current.user, id, payload)
