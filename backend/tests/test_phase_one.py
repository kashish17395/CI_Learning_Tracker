import io
from datetime import timedelta
import jwt
import pytest
from PIL import Image
from sqlalchemy import select
from conftest import PASSWORD, assignment, course, employee, login
from app.core.config import get_settings
from app.core.security import now
from app.models import AuditLog, Certificate, LearningAttempt, User
from app.services.common import today


def progress(client, attempt, status, **extra):
    return client.patch(
        "/api/v1/completions/" + attempt["id"],
        json={"status": status, "version": attempt["version"], **extra},
    )


def png():
    output = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(output, format="PNG")
    return output.getvalue()


def test_authentication_logout_and_protected_endpoint(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    result = login(client)
    assert result["role"] == "MANAGER"
    assert "password_hash" not in result
    token = client.cookies.get("lt_access")
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set("lt_access", token)
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize(
    "email,password",
    [("manager@example.com", "wrong"), ("unknown@example.com", PASSWORD)],
)
def test_invalid_login(client, email, password):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_rotation_and_reuse(manager):
    old = manager.cookies.get("lt_refresh")
    r = manager.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert manager.cookies.get("lt_refresh") != old
    manager.cookies.clear()
    manager.cookies.set("lt_refresh", old)
    assert manager.post("/api/v1/auth/refresh").status_code == 401


def test_csrf_and_origin(manager):
    assert (
        manager.post(
            "/api/v1/courses",
            json={"course_code": "X", "name": "X"},
            headers={"X-CSRF-Token": ""},
        ).status_code
        == 403
    )
    assert (
        manager.post(
            "/api/v1/courses",
            json={"course_code": "X", "name": "X"},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        manager.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": ""}).status_code
        == 403
    )


def test_passwords_hashed_and_employee_uniqueness(manager, db):
    e = employee(manager)
    user = db.scalar(select(User).where(User.id == e["user_id"]))
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash
    r = manager.post(
        "/api/v1/employees",
        json={
            "employee_code": "E002",
            "name": "Other",
            "email": "EMPLOYEE@example.com",
            "password": PASSWORD,
        },
    )
    assert r.status_code == 409


def test_course_creation_and_duplicate(manager):
    c = course(manager)
    assert c["estimated_duration_minutes"] == 60
    assert (
        manager.post(
            "/api/v1/courses", json={"course_code": "C001", "name": "Duplicate"}
        ).status_code
        == 409
    )


def test_employee_rbac_and_ownership(manager):
    e = employee(manager)
    other = employee(manager, "E002", "other@example.com")
    c = course(manager)
    owned = assignment(manager, e["id"], c["id"])
    foreign = assignment(manager, other["id"], c["id"])
    login(manager, "employee@example.com")
    assert manager.get("/api/v1/employees").status_code == 403
    assert (
        manager.post(
            "/api/v1/courses", json={"course_code": "NO", "name": "Forbidden"}
        ).status_code
        == 403
    )
    assert (
        manager.post(
            "/api/v1/assignments", json={"employee_id": e["id"], "course_id": c["id"]}
        ).status_code
        == 403
    )
    assert manager.get("/api/v1/dashboard/manager").status_code == 403
    assert manager.get("/api/v1/employees/" + other["id"]).status_code == 404
    assert (
        manager.get("/api/v1/employees/" + other["id"] + "/learning").status_code == 404
    )
    assert manager.get("/api/v1/assignments/" + foreign["id"]).status_code == 404
    assert (
        manager.get("/api/v1/completions/" + foreign["courses"][0]["id"]).status_code
        == 404
    )
    assert progress(manager, foreign["courses"][0], "ENROLLED").status_code == 404
    assert manager.get("/api/v1/assignments/" + owned["id"]).status_code == 200
    assert manager.get("/api/v1/my-learning").json()["total"] == 1


def test_track_relationship_order_snapshot_and_shared_attempt(manager, db):
    e = employee(manager)
    c1, c2 = course(manager), course(manager, "C002")
    r = manager.post(
        "/api/v1/learning-tracks",
        json={"name": "Engineering", "course_ids": [c2["id"], c1["id"]]},
    )
    assert r.status_code == 201
    track = r.json()
    assert [c["id"] for c in track["courses"]] == [c2["id"], c1["id"]]
    a = assignment(manager, e["id"], track_id=track["id"])
    direct = assignment(manager, e["id"], c1["id"])
    assert a["courses"][1]["id"] == direct["courses"][0]["id"]
    assert len(db.scalars(select(LearningAttempt)).all()) == 2
    assert (
        manager.put(
            "/api/v1/learning-tracks/" + track["id"] + "/courses",
            json={"course_ids": [c1["id"]]},
        ).status_code
        == 200
    )
    assert len(manager.get("/api/v1/assignments/" + a["id"]).json()["courses"]) == 2
    assert (
        manager.put(
            "/api/v1/learning-tracks/" + track["id"] + "/courses",
            json={"course_ids": [c1["id"], c1["id"]]},
        ).status_code
        == 422
    )


def test_employee_progress_completion_and_new_attempt(manager):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    login(manager, "employee@example.com")
    r = progress(manager, a, "ENROLLED")
    assert r.status_code == 200
    a = r.json()
    assert progress(manager, a, "NOT_STARTED").status_code == 422
    r = progress(manager, a, "IN_PROGRESS")
    assert r.status_code == 200
    a = r.json()
    assert (
        progress(
            manager, a, "COMPLETED", completion_date=str(today() + timedelta(days=1))
        ).status_code
        == 422
    )
    assert progress(manager, a, "COMPLETED").status_code == 422
    r = progress(manager, a, "COMPLETED", completion_date=str(today()))
    assert r.status_code == 200
    completed = r.json()
    assert progress(manager, completed, "IN_PROGRESS").status_code == 422
    login(manager)
    later = assignment(manager, e["id"], c["id"])
    assert later["courses"][0]["id"] != completed["id"]
    assert (
        progress(
            manager, completed, "IN_PROGRESS", reason="Correct completion"
        ).status_code
        == 409
    )


def test_certificate_requirement_and_metadata(manager, db):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"], certificate_required=True)["courses"][0]
    login(manager, "employee@example.com")
    assert (
        progress(manager, a, "COMPLETED", completion_date=str(today())).status_code
        == 422
    )
    r = manager.post(
        "/api/v1/certificates",
        data={"attempt_id": a["id"]},
        files={"file": ("../proof.png", png(), "image/png")},
    )
    assert r.status_code == 201, r.text
    cert = r.json()
    assert cert["original_filename"] == "proof.png"
    assert "blob_key" not in cert
    stored = db.get(Certificate, cert["id"])
    assert stored.blob_key.startswith("certificates/" + e["id"] + "/" + a["id"] + "/")
    assert stored.file_size == len(png())
    assert (
        manager.get("/api/v1/certificates/" + cert["id"] + "/download").content == png()
    )
    assert (
        progress(manager, a, "COMPLETED", completion_date=str(today())).status_code
        == 200
    )


@pytest.mark.parametrize(
    "filename,mime,content",
    [
        ("x.exe", "application/octet-stream", b"x"),
        ("x.png", "image/png", b"not image"),
        ("x.jpg", "image/png", b"bad"),
        ("x.pdf", "application/pdf", b"bad"),
    ],
)
def test_invalid_uploads(manager, filename, mime, content):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    assert (
        manager.post(
            "/api/v1/certificates",
            data={"attempt_id": a["id"]},
            files={"file": (filename, content, mime)},
        ).status_code
        == 422
    )


def test_foreign_certificate_access(manager):
    e, c = employee(manager), course(manager)
    employee(manager, "E002", "other@example.com")
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    r = manager.post(
        "/api/v1/certificates",
        data={"attempt_id": a["id"]},
        files={"file": ("proof.png", png(), "image/png")},
    )
    cert = r.json()
    login(manager, "other@example.com")
    assert manager.get("/api/v1/certificates").json()["total"] == 0
    assert (
        manager.get("/api/v1/certificates/" + cert["id"] + "/download").status_code
        == 404
    )
    assert (
        manager.post(
            "/api/v1/certificates",
            data={"attempt_id": a["id"]},
            files={"file": ("proof.png", png(), "image/png")},
        ).status_code
        == 404
    )


def test_shared_policies_restrict_completion(manager):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    assignment(manager, e["id"], c["id"], employee_can_complete=False)
    login(manager, "employee@example.com")
    assert progress(manager, a, "ENROLLED").status_code == 200
    a = manager.get("/api/v1/completions/" + a["id"]).json()
    assert (
        progress(manager, a, "COMPLETED", completion_date=str(today())).status_code
        == 403
    )


def test_dashboard_counts_deduplicate_and_derive_overdue(manager):
    e, c = employee(manager), course(manager)
    a = assignment(
        manager,
        e["id"],
        c["id"],
        target_date=str(today() - timedelta(days=1)),
        is_mandatory=True,
    )
    assignment(manager, e["id"], c["id"])
    data = manager.get("/api/v1/dashboard/manager").json()
    assert data["summary"]["assigned"] == 1
    assert data["summary"]["total_assignments"] == 2
    assert data["summary"]["overdue"] == 1
    assert len(data["priority_development"]) == 1
    assert (
        progress(
            manager,
            a["courses"][0],
            "COMPLETED",
            completion_date=str(today()),
            reason="Verified completion",
        ).status_code
        == 200
    )
    data = manager.get("/api/v1/dashboard/manager").json()
    assert data["summary"]["completion_percentage"] == 100
    assert data["summary"]["overdue"] == 0
    assert manager.get("/api/v1/assignments/" + a["id"]).json()["status"] == "COMPLETED"


def test_cancel_retire_preserves_history(manager):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])
    r = manager.patch(
        "/api/v1/assignments/" + a["id"],
        json={"version": a["version"], "cancel": True, "reason": "No longer required"},
    )
    assert r.status_code == 200
    assert (
        manager.get("/api/v1/employees/" + e["id"] + "/learning").json()["total"] == 1
    )
    new = assignment(manager, e["id"], c["id"])
    assert new["courses"][0]["id"] != a["courses"][0]["id"]


def test_deactivation_revokes_session(manager):
    e = employee(manager)
    login(manager, "employee@example.com")
    token = manager.cookies.get("lt_access")
    login(manager)
    assert (
        manager.patch(
            "/api/v1/employees/" + e["id"], json={"is_active": False}
        ).status_code
        == 200
    )
    manager.cookies.clear()
    manager.cookies.set("lt_access", token)
    assert manager.get("/api/v1/auth/me").status_code == 401
    assert (
        manager.post(
            "/api/v1/auth/login",
            json={"email": "employee@example.com", "password": PASSWORD},
        ).status_code
        == 401
    )


def test_stale_updates_audit_and_validation(manager, db):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    assert (
        progress(manager, a, "ENROLLED", reason="Verified enrolment").status_code == 200
    )
    assert (
        progress(manager, a, "IN_PROGRESS", reason="Update progress").status_code == 409
    )
    assert (
        manager.patch("/api/v1/courses/" + c["id"], json={"name": None}).status_code
        == 422
    )
    assert manager.get("/api/v1/courses?sort=password_hash").status_code == 422
    logs = db.scalars(select(AuditLog)).all()
    assert {
        "EMPLOYEE_CREATED",
        "COURSE_CREATED",
        "LEARNING_ASSIGNED",
        "STATUS_CHANGED",
    }.issubset({log.action for log in logs})
    assert PASSWORD not in str([log.details for log in logs])


def test_login_rate_limit(client):
    for _ in range(10):
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@example.com", "password": "wrong"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        ).status_code
        == 429
    )


def test_expired_access_refresh_and_tampering(manager, db):
    claims = jwt.decode(
        manager.cookies.get("lt_access"),
        get_settings().jwt_secret,
        algorithms=["HS256"],
    )
    claims["exp"] = now() - timedelta(seconds=1)
    manager.cookies.clear()
    manager.cookies.set(
        "lt_access", jwt.encode(claims, get_settings().jwt_secret, algorithm="HS256")
    )
    assert manager.get("/api/v1/auth/me").status_code == 401
    manager.cookies.set("lt_access", "invalid.token")
    assert manager.get("/api/v1/auth/me").status_code == 401


def test_certificate_upload_limit(manager, monkeypatch):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    assert (
        manager.post(
            "/api/v1/certificates",
            data={"attempt_id": a["id"]},
            files={"file": ("proof.png", png(), "image/png")},
        ).status_code
        == 413
    )


def test_track_patch_is_atomic(manager):
    c = course(manager)
    r = manager.post(
        "/api/v1/learning-tracks",
        json={"name": "Original track", "course_ids": [c["id"]]},
    )
    track = r.json()
    r = manager.patch(
        "/api/v1/learning-tracks/" + track["id"],
        json={"name": "Changed name", "course_ids": ["missing-course"]},
    )
    assert r.status_code == 404
    assert (
        manager.get("/api/v1/learning-tracks/" + track["id"]).json()["name"]
        == "Original track"
    )


def test_password_whitespace_is_preserved(manager):
    password = "  Significant spaces  "
    r = manager.post(
        "/api/v1/employees",
        json={
            "employee_code": "SPACE",
            "name": "Whitespace",
            "email": "space@example.com",
            "password": password,
        },
    )
    assert r.status_code == 201
    login(manager, "space@example.com", password)
    assert (
        manager.post(
            "/api/v1/auth/login",
            json={"email": "space@example.com", "password": password.strip()},
        ).status_code
        == 401
    )


def test_mandatory_overdue_uses_its_own_deadline(manager):
    e, c = employee(manager), course(manager)
    assignment(
        manager,
        e["id"],
        c["id"],
        target_date=str(today() - timedelta(days=1)),
        is_mandatory=False,
    )
    assignment(
        manager,
        e["id"],
        c["id"],
        target_date=str(today() + timedelta(days=1)),
        is_mandatory=True,
    )
    data = manager.get("/api/v1/dashboard/manager").json()
    assert data["summary"]["overdue"] == 1
    assert data["priority_development"] == []


def test_required_certificate_policy_cannot_invalidate_completion(manager):
    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])
    assert (
        progress(
            manager,
            a["courses"][0],
            "COMPLETED",
            completion_date=str(today()),
            reason="Verified learning",
        ).status_code
        == 200
    )
    r = manager.patch(
        "/api/v1/assignments/" + a["id"],
        json={
            "version": a["version"],
            "certificate_required": True,
            "reason": "Policy update",
        },
    )
    assert r.status_code == 422


def test_corrupt_image_checksum_returns_validation_error(manager):
    import base64

    e, c = employee(manager), course(manager)
    a = assignment(manager, e["id"], c["id"])["courses"][0]
    damaged = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a7S8AAAAASUVORK5CYII="
    )
    assert (
        manager.post(
            "/api/v1/certificates",
            data={"attempt_id": a["id"]},
            files={"file": ("proof.png", damaged, "image/png")},
        ).status_code
        == 422
    )


def test_chunked_requests_cannot_bypass_body_size_limit(client):
    request = client.build_request(
        "POST",
        "/api/v1/auth/login",
        content=iter([b"x" * (12 * 1024 * 1024)]),
        headers={"Content-Type": "application/json"},
    )
    request.headers.pop("content-length", None)
    response = client.send(request)
    assert response.status_code == 413
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.json()["error"]["request_id"]
