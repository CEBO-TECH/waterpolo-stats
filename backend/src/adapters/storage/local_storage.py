"""Filesystem-backed storage — used for local dev and tests."""

import os

from src.config import settings
from src.domain.ports.external import StoragePort


class LocalStorageAdapter(StoragePort):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or settings.VOICE_STORAGE_DIR

    def _path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def get_bytes(self, key: str) -> bytes | None:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)
