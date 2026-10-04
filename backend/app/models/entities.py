from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.core.security import now


def uid():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Entity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class User(Entity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16), default="EMPLOYEE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        CheckConstraint("role IN ('MANAGER','EMPLOYEE')", name="ck_user_role"),
    )


class Team(Entity, Base):
    __tablename__ = "teams"
    name: Mapped[str] = mapped_column(String(150), unique=True)
    manager_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Employee(Entity, Base):
    __tablename__ = "employees"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    employee_code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    department: Mapped[str] = mapped_column(String(150), default="", index=True)
    designation: Mapped[str] = mapped_column(String(150), default="")
    team_id: Mapped[str | None] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), index=True
    )


class AuthSession(Entity, Base):
    __tablename__ = "auth_sessions"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(Entity, Base):
    __tablename__ = "refresh_tokens"
    session_id: Mapped[str] = mapped_column(
        ForeignKey("auth_sessions.id", ondelete="RESTRICT"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="RESTRICT")
    )


class Course(Entity, Base):
    __tablename__ = "courses"
    course_code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    provider: Mapped[str] = mapped_column(String(150), default="")
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    __table_args__ = (
        CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes >= 0",
            name="ck_course_duration",
        ),
    )


class LearningTrack(Entity, Base):
    __tablename__ = "learning_tracks"
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class TrackCourse(Base):
    __tablename__ = "learning_track_courses"
    learning_track_id: Mapped[str] = mapped_column(
        ForeignKey("learning_tracks.id", ondelete="RESTRICT"), primary_key=True
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), primary_key=True
    )
    sequence_order: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("learning_track_id", "sequence_order", name="uq_track_order"),
        CheckConstraint("sequence_order > 0", name="ck_track_order"),
    )


class Assignment(Entity, Base):
    __tablename__ = "learning_assignments"
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    course_id: Mapped[str | None] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT")
    )
    learning_track_id: Mapped[str | None] = mapped_column(
        ForeignKey("learning_tracks.id", ondelete="RESTRICT")
    )
    assigned_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    target_date: Mapped[date | None] = mapped_column(Date, index=True)
    employee_can_update: Mapped[bool] = mapped_column(Boolean, default=True)
    employee_can_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    certificate_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        CheckConstraint(
            "(course_id IS NOT NULL AND learning_track_id IS NULL) OR (course_id IS NULL AND learning_track_id IS NOT NULL)",
            name="ck_assignment_target",
        ),
        UniqueConstraint("id", "employee_id", name="uq_assignment_employee"),
    )


class LearningAttempt(Entity, Base):
    __tablename__ = "course_learning_attempts"
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="NOT_STARTED", index=True)
    started_on: Mapped[date] = mapped_column(Date)
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    in_progress_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_date: Mapped[date | None] = mapped_column(Date)
    completed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        UniqueConstraint("id", "employee_id", "course_id", name="uq_attempt_identity"),
        CheckConstraint(
            "status IN ('NOT_STARTED','ENROLLED','IN_PROGRESS','COMPLETED')",
            name="ck_attempt_status",
        ),
        CheckConstraint(
            "(status = 'COMPLETED' AND completion_date IS NOT NULL AND completed_by IS NOT NULL) OR (status <> 'COMPLETED' AND completion_date IS NULL AND completed_by IS NULL)",
            name="ck_attempt_completion",
        ),
        Index(
            "uq_active_attempt",
            "employee_id",
            "course_id",
            unique=True,
            postgresql_where=text("status <> 'COMPLETED' AND retired_at IS NULL"),
            sqlite_where=text("status <> 'COMPLETED' AND retired_at IS NULL"),
        ),
    )


class AssignmentCourse(Entity, Base):
    __tablename__ = "assignment_courses"
    assignment_id: Mapped[str] = mapped_column(String(36), index=True)
    employee_id: Mapped[str] = mapped_column(String(36))
    course_id: Mapped[str] = mapped_column(String(36), index=True)
    learning_attempt_id: Mapped[str] = mapped_column(String(36), index=True)
    sequence_order: Mapped[int] = mapped_column(Integer)
    target_date_override: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (
        ForeignKeyConstraint(
            ["assignment_id", "employee_id"],
            ["learning_assignments.id", "learning_assignments.employee_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["learning_attempt_id", "employee_id", "course_id"],
            [
                "course_learning_attempts.id",
                "course_learning_attempts.employee_id",
                "course_learning_attempts.course_id",
            ],
            ondelete="RESTRICT",
        ),
        UniqueConstraint("assignment_id", "course_id", name="uq_assignment_course"),
        UniqueConstraint("assignment_id", "sequence_order", name="uq_assignment_order"),
        CheckConstraint("sequence_order > 0", name="ck_assignment_order"),
    )


class Certificate(Entity, Base):
    __tablename__ = "certificates"
    learning_attempt_id: Mapped[str] = mapped_column(
        ForeignKey("course_learning_attempts.id", ondelete="RESTRICT"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    blob_key: Mapped[str] = mapped_column(String(512), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    uploaded_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (CheckConstraint("file_size > 0", name="ck_certificate_size"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(
        "metadata", JSON().with_variant(JSONB(), "postgresql"), default=dict
    )
    request_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (
        Index("ix_audit_entity_date", "entity_type", "entity_id", "created_at"),
    )
