import os
import secrets
import tempfile

os.environ.update(
    DATABASE_URL="sqlite://",
    JWT_SECRET=secrets.token_urlsafe(48),
    STORAGE_BACKEND="local",
    STORAGE_ROOT=tempfile.mkdtemp(prefix="learning-tests-"),
    PUBLIC_ORIGIN="http://localhost:3000",
    REDIS_URL="",
    APP_ENV="development",
)
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.rate_limit import _attempts
from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models import Base, Employee, User

PASSWORD = "Correct-Passphrase-42"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(engine, expire_on_commit=False)
    with Session() as session:
        manager = User(
            email="manager@example.com",
            password_hash=hash_password(PASSWORD),
            role="MANAGER",
        )
        session.add(manager)
        session.flush()
        session.add(
            Employee(
                user_id=manager.id,
                employee_code="M001",
                name="Manager",
                department="Engineering",
            )
        )
        session.commit()
        yield session
    engine.dispose()


@pytest.fixture
def client(db):
    _attempts.clear()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as client:
        yield client
    app.dependency_overrides.clear()


def login(client, email="manager@example.com", password=PASSWORD):
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = client.cookies.get("lt_csrf")
    return response.json()


@pytest.fixture
def manager(client):
    login(client)
    return client


def employee(client, code="E001", email="employee@example.com"):
    response = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "name": "Employee " + code,
            "email": email,
            "password": PASSWORD,
            "department": "Engineering",
            "designation": "Engineer",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def course(client, code="C001"):
    response = client.post(
        "/api/v1/courses",
        json={
            "course_code": code,
            "name": "Course " + code,
            "category": "Technical",
            "estimated_duration_minutes": 60,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def assignment(client, employee_id, course_id=None, track_id=None, **extra):
    response = client.post(
        "/api/v1/assignments",
        json={
            "employee_id": employee_id,
            "course_id": course_id,
            "learning_track_id": track_id,
            **extra,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
