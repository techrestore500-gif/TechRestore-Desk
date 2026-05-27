from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.settings import Settings


@dataclass
class StorageObject:
    content: bytes
    content_type: str | None = None


class StorageProvider(Protocol):
    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        ...

    def get_object(self, *, key: str) -> StorageObject:
        ...

    def delete_object(self, *, key: str) -> None:
        ...

    def object_exists(self, *, key: str) -> bool:
        ...

    def iter_keys(self, *, prefix: str = "") -> list[str]:
        ...


class LocalStorageProvider:
    def __init__(self, root: Path):
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        normalized = key.replace("\\", "/").lstrip("/")
        path = (self._root / normalized).resolve()
        if not str(path).startswith(str(self._root.resolve())):
            raise ValueError("Invalid storage key path traversal")
        return path

    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def get_object(self, *, key: str) -> StorageObject:
        path = self._path_for(key)
        if not path.exists():
            raise FileNotFoundError("Object not found")
        return StorageObject(content=path.read_bytes(), content_type=None)

    def delete_object(self, *, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            path.unlink()

    def object_exists(self, *, key: str) -> bool:
        path = self._path_for(key)
        return path.exists()

    def iter_keys(self, *, prefix: str = "") -> list[str]:
        all_files = [path for path in self._root.rglob("*") if path.is_file()]
        keys = [str(path.relative_to(self._root)).replace("\\", "/") for path in all_files]
        if not prefix:
            return keys
        return [key for key in keys if key.startswith(prefix)]


class S3StorageProvider:
    def __init__(self, settings: Settings):
        try:
            import boto3
        except Exception as error:
            raise RuntimeError("boto3 is required for S3 storage provider") from error

        self._bucket = settings.attachments_bucket
        self._client = boto3.client(
            "s3",
            region_name=settings.attachments_region,
            endpoint_url=settings.attachments_endpoint_url,
            aws_access_key_id=settings.attachments_access_key_id,
            aws_secret_access_key=settings.attachments_secret_access_key,
        )

    def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    def get_object(self, *, key: str) -> StorageObject:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        stream = response.get("Body")
        content = stream.read() if stream else b""
        return StorageObject(content=content, content_type=response.get("ContentType"))

    def delete_object(self, *, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def object_exists(self, *, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    def iter_keys(self, *, prefix: str = "") -> list[str]:
        keys: list[str] = []
        continuation_token = None

        while True:
            kwargs = {
                "Bucket": self._bucket,
                "Prefix": prefix,
                "MaxKeys": 1000,
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            response = self._client.list_objects_v2(**kwargs)
            contents = response.get("Contents", [])
            keys.extend(item["Key"] for item in contents if item.get("Key"))

            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")

        return keys


def build_storage_provider(settings: Settings) -> StorageProvider:
    if settings.attachments_provider == "s3":
        return S3StorageProvider(settings)
    return LocalStorageProvider(settings.attachments_local_root)
