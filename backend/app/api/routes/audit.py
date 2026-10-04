from datetime import datetime
from fastapi import APIRouter, Depends
from app.api.params import paging
from app.db.session import get_db
from app.dependencies.auth import manager
from app.models import AuditLog, Team
from app.repositories.catalog import page
from app.schemas.requests import TeamCreate
from app.services.catalog import create_team
from app.services.common import dump

router = APIRouter(tags=["Administration"])


@router.get("/audit-logs")
def logs(
    actor_user_id: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    params=Depends(paging),
    current=Depends(manager),
    db=Depends(get_db),
):
    filters = []
    for column, value in (
        (AuditLog.actor_user_id, actor_user_id),
        (AuditLog.entity_id, entity_id),
        (AuditLog.action, action),
    ):
        if value:
            filters.append(column == value)
    if date_from:
        filters.append(AuditLog.created_at >= date_from)
    if date_to:
        filters.append(AuditLog.created_at <= date_to)
    rows, total = page(
        db,
        AuditLog,
        fields=("action", "entity_type"),
        filters=filters,
        allowed_sort=("created_at", "action"),
        **params
    )
    return {
        "items": [dump(r) for r in rows],
        "total": total,
        "page": params["page"],
        "page_size": params["page_size"],
    }


@router.get("/teams")
def teams(params=Depends(paging), current=Depends(manager), db=Depends(get_db)):
    rows, total = page(db, Team, fields=("name",), **params)
    return {
        "items": [dump(r) for r in rows],
        "total": total,
        "page": params["page"],
        "page_size": params["page_size"],
    }


@router.post("/teams", status_code=201)
def team(payload: TeamCreate, current=Depends(manager), db=Depends(get_db)):
    return create_team(db, current.user, payload)
