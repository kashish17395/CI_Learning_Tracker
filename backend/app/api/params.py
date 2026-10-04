from datetime import date
from fastapi import Query


def paging(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=200),
    sort: str = "created_at",
    direction: str = "desc",
):
    return dict(
        page=page, page_size=page_size, search=search, sort=sort, direction=direction
    )


def learning_filters(
    search: str = Query("", max_length=200),
    status: str | None = Query(
        None, pattern="^(NOT_STARTED|ENROLLED|IN_PROGRESS|COMPLETED|OVERDUE)$"
    ),
    course_id: str | None = None,
    track_id: str | None = None,
    department: str | None = None,
    target_from: date | None = None,
    target_to: date | None = None,
):
    return dict(
        search=search,
        status=status,
        course_id=course_id,
        track_id=track_id,
        department=department,
        target_from=target_from,
        target_to=target_to,
    )
