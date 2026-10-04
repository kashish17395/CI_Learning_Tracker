from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    app_env: str = "development"
    database_url: str = Field(repr=False)
    jwt_secret: str = Field(repr=False)
    public_origin: str = "http://localhost:3000"
    cookie_secure: bool = False
    organization_timezone: str = "Asia/Calcutta"
    access_minutes: int = 15
    refresh_days: int = 7
    storage_backend: str = "s3"
    storage_root: str = ".storage"
    s3_endpoint: str | None = None
    s3_bucket: str = "learning-certificates"
    s3_region: str = "us-east-1"
    s3_access_key: str | None = Field(default=None, repr=False)
    s3_secret_key: str | None = Field(default=None, repr=False)
    redis_url: str | None = Field(default=None, repr=False)
    max_upload_bytes: int = 10 * 1024 * 1024

    @model_validator(mode="after")
    def secure_configuration(self):
        if len(self.jwt_secret) < 32 or self.jwt_secret.startswith(
            ("REPLACE_", "SET_")
        ):
            raise ValueError("JWT_SECRET must contain at least 32 random characters")
        if self.app_env == "production":
            if not self.cookie_secure or not self.public_origin.startswith("https://"):
                raise ValueError("Production requires secure cookies and HTTPS")
            if not self.redis_url or self.storage_backend != "s3":
                raise ValueError("Production requires Redis and object storage")
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires PostgreSQL")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
