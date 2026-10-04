"""Isolated browser-test server. Never seeds a configured business database."""

import os
from pathlib import Path
import secrets


def main():
    if os.environ.get("BROWSER_TEST_MODE") != "1" or not os.environ.get(
        "TEST_BOOTSTRAP_PASSWORD"
    ):
        raise SystemExit("This server requires the explicit browser-test harness")
    root = Path(__file__).resolve().parents[2] / ".browser-tests"
    path = Path(os.environ["TEST_DATABASE_PATH"]).resolve()
    if root.resolve() not in path.parents or path.exists():
        raise SystemExit("Use a new test database within backend/.browser-tests")
    root.mkdir(parents=True, exist_ok=True)
    os.environ.update(
        DATABASE_URL="sqlite:///" + path.as_posix(),
        JWT_SECRET=secrets.token_urlsafe(48),
        APP_ENV="test",
        PUBLIC_ORIGIN="http://127.0.0.1:3100",
        COOKIE_SECURE="false",
        REDIS_URL="",
        STORAGE_BACKEND="local",
        STORAGE_ROOT=str(root / "objects"),
    )
    from app.db.session import engine, SessionLocal
    from app.models import Base, User, Employee
    from app.core.security import hash_password

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = User(
            email="manager@example.com",
            password_hash=hash_password(os.environ["TEST_BOOTSTRAP_PASSWORD"]),
            role="MANAGER",
        )
        db.add(user)
        db.flush()
        db.add(
            Employee(
                user_id=user.id,
                employee_code="MGR-TEST",
                name="Test Manager",
                department="Management",
            )
        )
        db.commit()
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8100, proxy_headers=False)


if __name__ == "__main__":
    main()
