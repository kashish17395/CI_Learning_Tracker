from sqlalchemy import select
from app.core.errors import AppError, invalid, missing
from app.core.security import now
from app.dependencies.auth import own_employee
from app.models import (
    Assignment,
    AssignmentCourse,
    Certificate,
    Course,
    Employee,
    LearningAttempt,
    LearningTrack,
    TrackCourse,
    User,
)
from app.repositories.catalog import get
from app.services.common import audit, dump, today

STATUSES = ["NOT_STARTED", "ENROLLED", "IN_PROGRESS", "COMPLETED"]


def active_contexts(db, attempt_id):
    return db.execute(
        select(AssignmentCourse, Assignment)
        .join(Assignment, Assignment.id == AssignmentCourse.assignment_id)
        .where(
            AssignmentCourse.learning_attempt_id == attempt_id,
            Assignment.cancelled_at.is_(None),
        )
    ).all()


def permitted_attempt(db, actor, id, *, lock=False):
    attempt = get(db, LearningAttempt, id, lock=lock)
    own_employee(db, actor, attempt.employee_id)
    return attempt


def evidence(db, attempt_id):
    return db.scalars(
        select(Certificate).where(
            Certificate.learning_attempt_id == attempt_id,
            Certificate.revoked_at.is_(None),
        )
    ).all()


def attempt_view(db, attempt):
    course = db.get(Course, attempt.course_id)
    contexts = active_contexts(db, attempt.id)
    dates = [
        item.target_date_override or assignment.target_date
        for item, assignment in contexts
    ]
    dates = [value for value in dates if value]
    due = min(dates) if dates else None
    employee = db.get(Employee, attempt.employee_id)
    return {
        **dump(attempt),
        "course": dump(course),
        "employee_name": employee.name,
        "department": employee.department,
        "target_date": due,
        "overdue": bool(due and due < today() and attempt.status != "COMPLETED"),
        "certificate_required": any(a.certificate_required for _, a in contexts),
        "employee_can_update": bool(contexts)
        and all(a.employee_can_update for _, a in contexts),
        "employee_can_complete": bool(contexts)
        and all(a.employee_can_complete for _, a in contexts),
        "certificates": [
            dump(cert, exclude=("blob_key",)) for cert in evidence(db, attempt.id)
        ],
        "assignments": [
            {
                "id": a.id,
                "target_date": item.target_date_override or a.target_date,
                "track_id": a.learning_track_id,
                "track_name": (
                    db.get(LearningTrack, a.learning_track_id).name
                    if a.learning_track_id
                    else None
                ),
                "is_mandatory": a.is_mandatory,
            }
            for item, a in contexts
        ],
    }


def assignment_view(db, actor, assignment):
    own_employee(db, actor, assignment.employee_id)
    items = db.scalars(
        select(AssignmentCourse)
        .where(AssignmentCourse.assignment_id == assignment.id)
        .order_by(AssignmentCourse.sequence_order)
    ).all()
    attempts = [db.get(LearningAttempt, item.learning_attempt_id) for item in items]
    statuses = [attempt.status for attempt in attempts]
    status = (
        "COMPLETED"
        if statuses and all(s == "COMPLETED" for s in statuses)
        else (
            "NOT_STARTED"
            if all(s == "NOT_STARTED" for s in statuses)
            else "ENROLLED" if all(s == "ENROLLED" for s in statuses) else "IN_PROGRESS"
        )
    )
    dates = [a.completion_date for a in attempts if a.completion_date]
    employee = db.get(Employee, assignment.employee_id)
    target = (
        db.get(Course, assignment.course_id)
        if assignment.course_id
        else db.get(LearningTrack, assignment.learning_track_id)
    )
    return {
        **dump(assignment),
        "name": target.name,
        "employee_name": employee.name,
        "department": employee.department,
        "status": status,
        "completion_date": max(dates) if status == "COMPLETED" else None,
        "overdue": not assignment.cancelled_at
        and any(
            (i.target_date_override or assignment.target_date)
            and (i.target_date_override or assignment.target_date) < today()
            and a.status != "COMPLETED"
            for i, a in zip(items, attempts)
        ),
        "courses": [
            {
                **attempt_view(db, attempt),
                "sequence_order": item.sequence_order,
                "assignment_target_date": item.target_date_override
                or assignment.target_date,
            }
            for item, attempt in zip(items, attempts)
        ],
    }


def create_assignment(db, actor, payload):
    # Employee row serializes creation/reopening for the same person in PostgreSQL.
    employee = get(db, Employee, payload.employee_id, lock=True)
    if not db.get(User, employee.user_id).is_active:
        invalid("Cannot assign learning to an inactive employee")
    if payload.learning_track_id:
        track = get(db, LearningTrack, payload.learning_track_id, lock=True)
        if not track.is_active:
            invalid("Track is inactive")
        course_ids = db.scalars(
            select(TrackCourse.course_id)
            .where(TrackCourse.learning_track_id == track.id)
            .order_by(TrackCourse.sequence_order)
        ).all()
        if not course_ids:
            invalid("Track has no courses")
    else:
        course_ids = [payload.course_id]
    for id in course_ids:
        if not get(db, Course, id).is_active:
            invalid("Cannot assign inactive courses")
    assignment = Assignment(**payload.model_dump(), assigned_by=actor.id)
    db.add(assignment)
    db.flush()
    for sequence, id in enumerate(course_ids, 1):
        attempt = db.scalar(
            select(LearningAttempt).where(
                LearningAttempt.employee_id == employee.id,
                LearningAttempt.course_id == id,
                LearningAttempt.status != "COMPLETED",
                LearningAttempt.retired_at.is_(None),
            )
        )
        if not attempt:
            attempt = LearningAttempt(
                employee_id=employee.id, course_id=id, started_on=today()
            )
            db.add(attempt)
            db.flush()
        db.add(
            AssignmentCourse(
                assignment_id=assignment.id,
                employee_id=employee.id,
                course_id=id,
                learning_attempt_id=attempt.id,
                sequence_order=sequence,
            )
        )
    audit(db, actor, "LEARNING_ASSIGNED", assignment, {"course_ids": course_ids})
    db.commit()
    return assignment_view(db, actor, assignment)


def patch_assignment(db, actor, id, payload):
    assignment = get(db, Assignment, id, lock=True)
    get(db, Employee, assignment.employee_id, lock=True)
    if assignment.version != payload.version:
        raise AppError(
            409, "STALE_VERSION", "Assignment changed. Reload and try again."
        )
    if assignment.cancelled_at:
        invalid("Cancelled assignments cannot be modified")
    before = {"target_date": str(assignment.target_date), "version": assignment.version}
    for key, value in payload.model_dump(
        exclude_unset=True, exclude={"version", "cancel", "reason"}
    ).items():
        if value is None and key != "target_date":
            invalid(f"{key} cannot be null")
        setattr(assignment, key, value)
    if assignment.certificate_required and not payload.cancel:
        for item in db.scalars(
            select(AssignmentCourse).where(AssignmentCourse.assignment_id == id)
        ):
            attempt = db.get(LearningAttempt, item.learning_attempt_id)
            if attempt.status == "COMPLETED" and not evidence(db, attempt.id):
                invalid(
                    "Upload evidence for completed courses before requiring certificates"
                )
    if payload.cancel:
        assignment.cancelled_at, assignment.cancelled_by = now(), actor.id
        assignment.cancellation_reason = payload.reason
        db.flush()
        for item in db.scalars(
            select(AssignmentCourse).where(AssignmentCourse.assignment_id == id)
        ):
            attempt = db.get(LearningAttempt, item.learning_attempt_id)
            if attempt.status != "COMPLETED" and not active_contexts(db, attempt.id):
                attempt.retired_at = now()
    assignment.version += 1
    audit(
        db,
        actor,
        "ASSIGNMENT_CANCELLED" if payload.cancel else "ASSIGNMENT_UPDATED",
        assignment,
        {
            "reason": payload.reason,
            "before": before,
            "fields": list(payload.model_fields_set),
        },
    )
    db.commit()
    return assignment_view(db, actor, assignment)


def update_progress(db, actor, id, payload):
    attempt = permitted_attempt(db, actor, id)
    get(db, Employee, attempt.employee_id, lock=True)
    attempt = get(db, LearningAttempt, id, lock=True)
    if attempt.version != payload.version:
        raise AppError(409, "STALE_VERSION", "Progress changed. Reload and try again.")
    contexts = active_contexts(db, attempt.id)
    if not contexts or attempt.retired_at:
        invalid("No active assignment permits updates")
    if actor.role == "EMPLOYEE":
        if not all(a.employee_can_update for _, a in contexts):
            raise AppError(
                403, "PROGRESS_LOCKED", "Progress is managed by your manager"
            )
        if attempt.status == "COMPLETED":
            invalid("Ask your manager to correct completed learning")
        if STATUSES.index(payload.status) < STATUSES.index(attempt.status):
            invalid("Progress cannot move backwards")
        if payload.status == "COMPLETED" and not all(
            a.employee_can_complete for _, a in contexts
        ):
            raise AppError(
                403, "COMPLETION_LOCKED", "Completion must be recorded by your manager"
            )
    elif not payload.reason:
        invalid("Managers must provide a change reason")
    if payload.status == "COMPLETED":
        if (
            not payload.completion_date
            or not attempt.started_on <= payload.completion_date <= today()
        ):
            invalid(
                "Completion date must fall between the attempt start date and today"
            )
        if any(a.certificate_required for _, a in contexts) and not evidence(
            db, attempt.id
        ):
            invalid("Upload a certificate before completing this course")
    elif payload.completion_date:
        invalid("Completion date is only allowed for completed learning")
    if attempt.status == "COMPLETED" and payload.status != "COMPLETED":
        existing = db.scalar(
            select(LearningAttempt).where(
                LearningAttempt.employee_id == attempt.employee_id,
                LearningAttempt.course_id == attempt.course_id,
                LearningAttempt.status != "COMPLETED",
                LearningAttempt.retired_at.is_(None),
                LearningAttempt.id != attempt.id,
            )
        )
        if existing:
            raise AppError(
                409,
                "ACTIVE_ATTEMPT_EXISTS",
                "Another active attempt exists for this course",
            )
        # Evidence must be reaffirmed after reopening, rather than silently reused.
        for cert in evidence(db, attempt.id):
            cert.revoked_at, cert.revoked_by, cert.revocation_reason = (
                now(),
                actor.id,
                "Learning reopened: " + payload.reason,
            )
            audit(
                db,
                actor,
                "CERTIFICATE_REVOKED",
                cert,
                {"reason": cert.revocation_reason},
            )
    previous = {
        "status": attempt.status,
        "completion_date": str(attempt.completion_date),
    }
    attempt.status = payload.status
    if (
        payload.status in ("ENROLLED", "IN_PROGRESS", "COMPLETED")
        and not attempt.enrolled_at
    ):
        attempt.enrolled_at = now()
    if payload.status in ("IN_PROGRESS", "COMPLETED") and not attempt.in_progress_at:
        attempt.in_progress_at = now()
    attempt.completion_date = (
        payload.completion_date if payload.status == "COMPLETED" else None
    )
    attempt.completed_by = actor.id if payload.status == "COMPLETED" else None
    attempt.version += 1
    audit(
        db,
        actor,
        "COMPLETION_RECORDED" if payload.status == "COMPLETED" else "STATUS_CHANGED",
        attempt,
        {
            "before": previous,
            "status": payload.status,
            "completion_date": str(attempt.completion_date),
            "reason": payload.reason,
        },
    )
    db.commit()
    return attempt_view(db, attempt)


def learning_rows(db, actor, employee_id=None, *, history=False):
    if actor.role != "MANAGER":
        employee = db.scalar(select(Employee).where(Employee.user_id == actor.id))
        if not employee:
            return []
        if employee_id and employee_id != employee.id:
            missing()
        employee_id = employee.id
    if employee_id:
        own_employee(db, actor, employee_id)
    query = select(LearningAttempt)
    if employee_id:
        query = query.where(LearningAttempt.employee_id == employee_id)
    if not history:
        query = query.where(
            LearningAttempt.id.in_(
                select(AssignmentCourse.learning_attempt_id)
                .join(Assignment, Assignment.id == AssignmentCourse.assignment_id)
                .where(Assignment.cancelled_at.is_(None))
            )
        )
    return [
        attempt_view(db, attempt)
        for attempt in db.scalars(query.order_by(LearningAttempt.created_at.desc()))
    ]


def filter_rows(
    rows,
    *,
    search="",
    status=None,
    course_id=None,
    track_id=None,
    department=None,
    target_from=None,
    target_to=None,
):
    return [
        row
        for row in rows
        if (
            not search
            or search.lower()
            in (
                row.get("employee_name", "")
                + " "
                + row.get("name", "")
                + " "
                + row.get("course", {}).get("name", "")
            ).lower()
        )
        and (
            not status
            or (row["overdue"] if status == "OVERDUE" else row["status"] == status)
        )
        and (
            not course_id
            or row.get("course_id") == course_id
            or any(c["course_id"] == course_id for c in row.get("courses", []))
        )
        and (
            not track_id
            or row.get("learning_track_id") == track_id
            or any(a["track_id"] == track_id for a in row.get("assignments", []))
        )
        and (not department or row.get("department") == department)
        and (
            not target_from
            or row.get("target_date")
            and row["target_date"] >= target_from
        )
        and (
            not target_to or row.get("target_date") and row["target_date"] <= target_to
        )
    ]


def slice_rows(rows, page=1, page_size=20):
    return {
        "items": rows[(page - 1) * page_size : page * page_size],
        "total": len(rows),
        "page": page,
        "page_size": page_size,
    }
