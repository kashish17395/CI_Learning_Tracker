"""Opt-in PostgreSQL checks. Each run creates and drops only its random test schema."""

import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from app.core.errors import AppError
from app.core.security import hash_password
from app.models import AuditLog, Employee, LearningAttempt, User
from app.schemas.requests import AssignmentCreate, CourseCreate
from app.services import auth, catalog, learning

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_POSTGRES_URL"), reason="TEST_POSTGRES_URL not configured"
)


@pytest.fixture
def pg():
    url = os.environ["TEST_POSTGRES_URL"]
    schema = "tracker_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": "-csearch_path=" + schema})
    migration_path = (
        Path(__file__).parents[1]
        / "alembic/versions/099ba6615cba_initial_phase_1_learning_tracker_schema.py"
    )
    spec = importlib.util.spec_from_file_location("initial_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with engine.begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
    Session = sessionmaker(engine, expire_on_commit=False)
    with Session() as db:
        actor = User(
            email="manager@example.com",
            password_hash=hash_password("Integration-Passphrase-42"),
            role="MANAGER",
        )
        db.add(actor)
        db.flush()
        employee = Employee(
            user_id=actor.id, employee_code="PG1", name="Integration Manager"
        )
        db.add(employee)
        db.commit()
        c = catalog.create_course(
            db, actor, CourseCreate(course_code="PG1", name="Concurrent course")
        )
        ids = (actor.id, employee.id, c["id"])
    try:
        yield Session, ids
    finally:
        engine.dispose()
        with admin.begin() as connection:
            # schema is a generated fixed-prefix hex identifier, never user input.
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_concurrent_assignments_share_attempt(pg):
    Session, (actor_id, employee_id, course_id) = pg

    def assign(_):
        with Session() as db:
            return learning.create_assignment(
                db,
                db.get(User, actor_id),
                AssignmentCreate(employee_id=employee_id, course_id=course_id),
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assignments = list(pool.map(assign, range(2)))
    assert assignments[0]["courses"][0]["id"] == assignments[1]["courses"][0]["id"]
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(LearningAttempt)) == 1


def test_concurrent_refresh_reuse_revokes_session(pg):
    Session, _ = pg
    with Session() as db:
        _, _, token, csrf = auth.login(
            db, "manager@example.com", "Integration-Passphrase-42"
        )

    def rotate(_):
        with Session() as db:
            try:
                auth.refresh(db, token, csrf)
                return "OK"
            except AppError as error:
                return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(rotate, range(2)))
    assert sorted(outcomes) == ["OK", "TOKEN_REUSE"]


def test_audit_is_append_only(pg):
    Session, _ = pg
    with Session() as db:
        id = db.scalar(select(AuditLog.id))
        with pytest.raises(DBAPIError):
            db.execute(
                text("UPDATE audit_logs SET action=:action WHERE id=:id"),
                {"action": "TAMPER", "id": id},
            )
        db.rollback()
        with pytest.raises(DBAPIError):
            db.execute(text("DELETE FROM audit_logs WHERE id=:id"), {"id": id})
