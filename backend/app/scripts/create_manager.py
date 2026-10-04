from getpass import getpass
from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select, text
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Employee, User
from app.services.common import audit


def main():
    name = input("Name: ").strip()
    email = str(TypeAdapter(EmailStr).validate_python(input("Email: ").strip())).lower()
    password = getpass("Password (minimum 12 characters): ")
    if not name or len(name) > 150 or len(password) < 12 or len(password) > 256:
        raise SystemExit("Invalid name or password length")
    if password != getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    with SessionLocal() as db:
        if db.bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(752911042)"))
        if db.scalar(select(User).where(User.role == "MANAGER")):
            raise SystemExit("Initial manager already exists. Bootstrap is disabled.")
        user = User(email=email, password_hash=hash_password(password), role="MANAGER")
        db.add(user)
        db.flush()
        employee = Employee(
            user_id=user.id,
            employee_code="MGR-" + user.id[:8],
            name=name,
            department="Management",
            designation="Manager",
        )
        db.add(employee)
        db.flush()
        audit(db, user, "INITIAL_MANAGER_CREATED", employee)
        db.commit()
    print("Initial manager created. Sign in with the credentials you provided.")


if __name__ == "__main__":
    main()
