import secrets
import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_invalid_production_configuration_does_not_print_secrets():
    secret = secrets.token_urlsafe(48)
    with pytest.raises(ValidationError) as error:
        Settings(
            app_env="production",
            database_url="sqlite://",
            jwt_secret=secret,
            public_origin="http://localhost:3000",
            cookie_secure=False,
        )
    assert secret not in str(error.value)
    assert "Production requires secure cookies and HTTPS" in str(error.value)


def test_configuration_repr_hides_database_and_storage_secrets():
    secret = secrets.token_urlsafe(48)
    settings = Settings(
        database_url="postgresql+psycopg://user:PRIVATE_PASSWORD@localhost/database",
        jwt_secret=secret,
        s3_secret_key="PRIVATE_STORAGE_KEY",
    )
    assert secret not in repr(settings)
    assert "PRIVATE_PASSWORD" not in repr(settings)
    assert "PRIVATE_STORAGE_KEY" not in repr(settings)
