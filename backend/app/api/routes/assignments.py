from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.api.params import learning_filters, paging
from app.core.errors import invalid
from app.db.session import get_db
from app.dependencies.auth import identity, manager
from app.models import Assignment
from app.repositories.catalog import get
from app.schemas.requests import AssignmentCreate, AssignmentPatch
from app.services import learning

router = APIRouter(prefix="/assignments", tags=["Assignments"])
my_router = APIRouter(tags=["My learning"])


@router.get("")
def listing(
    employee_id: str | None = None,
    include_cancelled: bool = False,
    filters=Depends(learning_filters),
    params=Depends(paging),
    current=Depends(manager),
    db=Depends(get_db),
):
    query = select(Assignment)
    if employee_id:
        query = query.where(Assignment.employee_id == employee_id)
    if not include_cancelled:
        query = query.where(Assignment.cancelled_at.is_(None))
    rows = [
        learning.assignment_view(db, current.user, a)
        for a in db.scalars(query.order_by(Assignment.assigned_at.desc()))
    ]
    rows = learning.filter_rows(rows, **filters)
    sort = params["sort"]
    if sort not in ("created_at", "name", "target_date", "employee_name") or params[
        "direction"
    ] not in ("asc", "desc"):
        invalid("Unsupported sort field or direction")
    rows.sort(
        key=lambda row: (row.get(sort) is None, str(row.get(sort) or "")),
        reverse=params["direction"] == "desc",
    )
    return learning.slice_rows(rows, params["page"], params["page_size"])


@router.post("", status_code=201)
def create(payload: AssignmentCreate, current=Depends(manager), db=Depends(get_db)):
    return learning.create_assignment(db, current.user, payload)


@router.get("/{id}")
def detail(id: str, current=Depends(identity), db=Depends(get_db)):
    return learning.assignment_view(db, current.user, get(db, Assignment, id))


@router.patch("/{id}")
def patch(
    id: str, payload: AssignmentPatch, current=Depends(manager), db=Depends(get_db)
):
    return learning.patch_assignment(db, current.user, id, payload)


@my_router.get("/my-learning")
def mine(
    history: bool = False,
    filters=Depends(learning_filters),
    params=Depends(paging),
    current=Depends(identity),
    db=Depends(get_db),
):
    # A manager's personal endpoint must also be limited to their own profile.
    from app.dependencies.auth import employee_for

    employee = employee_for(db, current.user)
    rows = (
        learning.learning_rows(db, current.user, employee.id, history=history)
        if employee
        else []
    )
    return learning.slice_rows(
        learning.filter_rows(rows, **filters), params["page"], params["page_size"]
    )


@my_router.get("/my-learning/options")
def options(current=Depends(identity), db=Depends(get_db)):
    from app.dependencies.auth import employee_for

    employee = employee_for(db, current.user)
    rows = (
        learning.learning_rows(db, current.user, employee.id, history=True)
        if employee
        else []
    )
    courses = {
        row["course_id"]: {"id": row["course_id"], "name": row["course"]["name"]}
        for row in rows
    }
    tracks = {
        context["track_id"]: {"id": context["track_id"], "name": context["track_name"]}
        for row in rows
        for context in row["assignments"]
        if context["track_id"]
    }
    return {
        "courses": sorted(courses.values(), key=lambda c: c["name"]),
        "tracks": sorted(tracks.values(), key=lambda t: t["name"]),
    }
