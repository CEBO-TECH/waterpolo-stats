"""Object storage adapters for voice-note audio."""

from src.config import settings
from src.domain.ports.external import StoragePort

from .local_storage import LocalStorageAdapter


_instance: StoragePort | None = None


def get_storage() -> StoragePort:
    """Select the configured storage backend ('local' for dev/test, 's3' for prod)."""
    global _instance
    if _instance is None:
        if settings.STORAGE_BACKEND == "s3":
            from .s3_storage import S3StorageAdapter  # lazy import (boto3 only in prod)
            _instance = S3StorageAdapter()
        else:
            _instance = LocalStorageAdapter()
    return _instance


__all__ = ["get_storage", "LocalStorageAdapter"]
