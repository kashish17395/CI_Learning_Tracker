from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.api.params import learning_filters, paging
from app.db.session import get_db
from app.dependencies.auth import identity, manager, own_employee
from app.models import Employee, User
from app.repositories.catalog import page
from app.schemas.requests import EmployeeCreate, EmployeePatch
from app.services import catalog, learning

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("")
def list_employees(
    params=Depends(paging),
    department: str | None = None,
    active: bool | None = None,
    current=Depends(manager),
    db=Depends(get_db),
):
    filters = []
    if department:
        filters.append(Employee.department == department)
    if active is not None:
        filters.append(
            Employee.user_id.in_(select(User.id).where(User.is_active == active))
        )
    rows, total = page(
        db,
        Employee,
        fields=("name", "employee_code", "department"),
        filters=filters,
        allowed_sort=("created_at", "name", "employee_code", "department"),
        **params
    )
    return {
        "items": [catalog.employee_view(db, e) for e in rows],
        "total": total,
        "page": params["page"],
        "page_size": params["page_size"],
    }


@router.post("", status_code=201)
def create(payload: EmployeeCreate, current=Depends(manager), db=Depends(get_db)):
    return catalog.create_employee(db, current.user, payload)


@router.get("/{id}")
def detail(id: str, current=Depends(identity), db=Depends(get_db)):
    return catalog.employee_view(db, own_employee(db, current.user, id))


@router.patch("/{id}")
def patch(
    id: str, payload: EmployeePatch, current=Depends(manager), db=Depends(get_db)
):
    return catalog.patch_employee(db, current.user, id, payload)


@router.get("/{id}/learning")
def history(
    id: str,
    filters=Depends(learning_filters),
    params=Depends(paging),
    current=Depends(identity),
    db=Depends(get_db),
):
    rows = learning.filter_rows(
        learning.learning_rows(db, current.user, id, history=True), **filters
    )
    return learning.slice_rows(rows, params["page"], params["page_size"])
