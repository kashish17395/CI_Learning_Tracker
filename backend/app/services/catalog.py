from sqlalchemy import delete, select
from app.core.errors import invalid
from app.core.security import hash_password, now
from app.models import (
    AuthSession,
    Course,
    Employee,
    LearningTrack,
    Team,
    TrackCourse,
    User,
)
from app.repositories.catalog import get
from app.services.common import audit, changes, dump


def employee_view(db, employee):
    user = db.get(User, employee.user_id)
    team = db.get(Team, employee.team_id) if employee.team_id else None
    return {
        **dump(employee),
        "email": user.email,
        "is_active": user.is_active,
        "team_name": team.name if team else None,
    }


def validate_team(db, team_id):
    if team_id and not get(db, Team, team_id).is_active:
        invalid("Team is inactive")


def create_employee(db, actor, payload):
    validate_team(db, payload.team_id)
    user = User(
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role="EMPLOYEE",
    )
    db.add(user)
    db.flush()
    employee = Employee(
        user_id=user.id, **payload.model_dump(exclude={"email", "password"})
    )
    db.add(employee)
    db.flush()
    audit(db, actor, "EMPLOYEE_CREATED", employee)
    db.commit()
    return employee_view(db, employee)


def patch_employee(db, actor, employee_id, payload):
    employee = get(db, Employee, employee_id, lock=True)
    values = changes(payload, nullable=("team_id",))
    if "team_id" in values:
        validate_team(db, values["team_id"])
    user = get(db, User, employee.user_id, lock=True)
    if "email" in values:
        user.email = str(values.pop("email")).lower()
    if "is_active" in values:
        active = values.pop("is_active")
        if user.role == "MANAGER" and not active:
            invalid(
                "Manager accounts cannot be deactivated through employee management"
            )
        user.is_active = active
        if not active:
            for session in db.scalars(
                select(AuthSession).where(
                    AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)
                )
            ):
                session.revoked_at = now()
    for key, value in values.items():
        setattr(employee, key, value)
    audit(
        db,
        actor,
        "EMPLOYEE_UPDATED",
        employee,
        {"fields": list(payload.model_fields_set)},
    )
    db.commit()
    return employee_view(db, employee)


def create_course(db, actor, payload):
    course = Course(**payload.model_dump(), created_by=actor.id)
    db.add(course)
    db.flush()
    audit(db, actor, "COURSE_CREATED", course)
    db.commit()
    return dump(course)


def patch_course(db, actor, id, payload):
    course = get(db, Course, id, lock=True)
    for key, value in changes(
        payload, nullable=("estimated_duration_minutes",)
    ).items():
        setattr(course, key, value)
    audit(
        db, actor, "COURSE_UPDATED", course, {"fields": list(payload.model_fields_set)}
    )
    db.commit()
    return dump(course)


def track_view(db, track):
    memberships = db.scalars(
        select(TrackCourse)
        .where(TrackCourse.learning_track_id == track.id)
        .order_by(TrackCourse.sequence_order)
    ).all()
    return {
        **dump(track),
        "courses": [
            {
                **dump(db.get(Course, member.course_id)),
                "sequence_order": member.sequence_order,
            }
            for member in memberships
        ],
    }


def replace_courses(db, track, course_ids):
    if len(course_ids) != len(set(course_ids)):
        invalid("Duplicate track courses are not allowed")
    for id in course_ids:
        if not get(db, Course, id).is_active:
            invalid("Tracks can only include active courses")
    db.execute(delete(TrackCourse).where(TrackCourse.learning_track_id == track.id))
    db.flush()
    for position, id in enumerate(course_ids, 1):
        db.add(
            TrackCourse(
                learning_track_id=track.id, course_id=id, sequence_order=position
            )
        )


def create_track(db, actor, payload):
    track = LearningTrack(
        name=payload.name, description=payload.description, created_by=actor.id
    )
    db.add(track)
    db.flush()
    replace_courses(db, track, payload.course_ids)
    audit(db, actor, "TRACK_CREATED", track, {"course_ids": payload.course_ids})
    db.commit()
    return track_view(db, track)


def patch_track(db, actor, id, payload):
    track = get(db, LearningTrack, id, lock=True)
    values = changes(payload)
    course_ids = values.pop("course_ids", None)
    if course_ids is not None:
        replace_courses(db, track, course_ids)
    for key, value in values.items():
        setattr(track, key, value)
    audit(db, actor, "TRACK_UPDATED", track, {"fields": list(payload.model_fields_set)})
    db.commit()
    return track_view(db, track)


def update_track_courses(db, actor, id, payload):
    track = get(db, LearningTrack, id, lock=True)
    replace_courses(db, track, payload.course_ids)
    audit(db, actor, "TRACK_COURSES_CHANGED", track, {"course_ids": payload.course_ids})
    db.commit()
    return track_view(db, track)


def create_team(db, actor, payload):
    if (
        payload.manager_user_id
        and get(db, User, payload.manager_user_id).role != "MANAGER"
    ):
        invalid("Team manager must have the MANAGER role")
    team = Team(**payload.model_dump())
    db.add(team)
    db.flush()
    audit(db, actor, "TEAM_CREATED", team)
    db.commit()
    return dump(team)
