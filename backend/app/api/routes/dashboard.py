from fastapi import APIRouter, Depends
from app.api.params import learning_filters, paging
from app.db.session import get_db
from app.dependencies.auth import identity, manager
from app.services.dashboard import dashboard
from app.services.learning import slice_rows

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/me")
def personal(
    filters=Depends(learning_filters), current=Depends(identity), db=Depends(get_db)
):
    return dashboard(db, current.user, filters, personal=True)


@router.get("/manager")
def organization(
    employee_id: str | None = None,
    filters=Depends(learning_filters),
    current=Depends(manager),
    db=Depends(get_db),
):
    return dashboard(db, current.user, {**filters, "employee_id": employee_id})


@router.get("/capability-gaps")
def gaps(
    filters=Depends(learning_filters),
    params=Depends(paging),
    current=Depends(manager),
    db=Depends(get_db),
):
    result = dashboard(db, current.user, filters)
    return slice_rows(result["capability_gaps"], params["page"], params["page_size"])
