"""File storage backend for CV uploads."""

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles


class StorageBackend(ABC):
    """Abstract interface for file storage. Allows swapping local → S3 etc."""

    @abstractmethod
    async def save(self, content: bytes, filename: str) -> str:
        """Save file content. Returns the storage path."""

    @abstractmethod
    async def retrieve(self, path: str) -> bytes:
        """Retrieve file content by storage path."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete a file by storage path."""


class LocalStorageBackend(StorageBackend):
    """Stores files on the local filesystem under upload_dir."""

    def __init__(self, upload_dir: str) -> None:
        self._upload_dir = Path(upload_dir)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = self._upload_dir / unique_name

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return str(file_path)

    async def retrieve(self, path: str) -> bytes:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> None:
        file_path = Path(path)
        if file_path.exists():
            os.remove(file_path)
