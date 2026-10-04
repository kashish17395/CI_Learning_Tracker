from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.inspection import inspect
from app.core.config import get_settings
from app.core.errors import invalid
from app.models import AuditLog


def today():
    return datetime.now(ZoneInfo(get_settings().organization_timezone)).date()


def dump(entity, exclude=()):
    return {
        column.key: getattr(entity, column.key)
        for column in inspect(entity).mapper.column_attrs
        if column.key not in exclude
    }


def audit(db, actor, action, entity, details=None):
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=entity.id,
            details=details or {},
            request_id=db.info.get("request_id"),
        )
    )


def changes(payload, nullable=()):
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        if value is None and key not in nullable:
            invalid(f"{key} cannot be null")
    return values
