from sqlalchemy import func, or_, select
from app.core.errors import invalid, missing


def get(db, model, id, *, lock=False):
    query = select(model).where(model.id == id)
    if lock:
        query = query.with_for_update()
    value = db.scalar(query)
    if value is None:
        missing()
    return value


def page(
    db,
    model,
    *,
    search="",
    fields=(),
    filters=(),
    page=1,
    page_size=20,
    sort="created_at",
    direction="desc",
    allowed_sort=("created_at", "name")
):
    if sort not in allowed_sort or direction not in ("asc", "desc"):
        invalid("Unsupported sort field or direction")
    query = select(model).where(*filters)
    if search and fields:
        # Escape LIKE metacharacters: search is a literal substring.
        pattern = (
            "%"
            + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            + "%"
        )
        query = query.where(
            or_(*(getattr(model, f).ilike(pattern, escape="\\") for f in fields))
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    column = getattr(model, sort)
    query = query.order_by(
        column.desc() if direction == "desc" else column.asc(), model.id
    )
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return items, total
