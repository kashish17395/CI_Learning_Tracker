from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
import boto3
from app.core.config import get_settings


class StorageService(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str): ...

    @abstractmethod
    def download(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str): ...

    @abstractmethod
    def get_signed_url(self, key: str, expires: int = 60) -> str: ...


class S3Storage(StorageService):
    def __init__(self):
        settings = get_settings()
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    def upload(self, key, data, content_type):
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data, ContentType=content_type
        )

    def download(self, key):
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        try:
            return response["Body"].read()
        finally:
            response["Body"].close()

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def get_signed_url(self, key, expires=60):
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires
        )


class LocalStorage(StorageService):
    """Development/test adapter. Production configuration requires S3."""

    def __init__(self):
        self.root = Path(get_settings().storage_root).resolve()

    def path(self, key):
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid object key")
        return path

    def upload(self, key, data, content_type):
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def download(self, key):
        return self.path(key).read_bytes()

    def delete(self, key):
        self.path(key).unlink(missing_ok=True)

    def get_signed_url(self, key, expires=60):
        raise NotImplementedError(
            "Local files are served through authorized API downloads"
        )


@lru_cache
def storage():
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorage()
    if settings.storage_backend == "s3":
        return S3Storage()
    raise ValueError("Unknown storage backend")
