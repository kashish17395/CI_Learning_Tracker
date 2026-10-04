"""Generate independent development secrets without overwriting configuration."""

from pathlib import Path
import secrets


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    if target.exists():
        raise SystemExit(".env already exists; preserving its configuration")
    values = {
        "POSTGRES_PASSWORD": secrets.token_urlsafe(36),
        "JWT_SECRET": secrets.token_urlsafe(64),
        "S3_ACCESS_KEY": secrets.token_urlsafe(18),
        "S3_SECRET_KEY": secrets.token_urlsafe(48),
        "PUBLIC_ORIGIN": "http://localhost:3000",
        "COOKIE_SECURE": "false",
        "APP_ENV": "development",
    }
    with target.open("x", encoding="utf-8") as file:
        file.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
    target.chmod(0o600)
    print(
        "Created .env with independent random development secrets. No account was created."
    )


if __name__ == "__main__":
    main()
