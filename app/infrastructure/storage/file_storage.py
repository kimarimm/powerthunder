"""Реализация файлового хранилища."""

import os
from pathlib import Path
from typing import BinaryIO

from app.domain.interfaces.file_repository import IFileStorage
from app.infrastructure.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_ROOT = Path(settings.storage_root) if settings.storage_root else BASE_DIR / "uploads"


class LocalFileStorage(IFileStorage):
    """Локальное файловое хранилище."""

    def __init__(self, root: Path = STORAGE_ROOT):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, path: str) -> Path:
        return self.root / path

    async def save(self, path: str, content: BinaryIO, size: int) -> str:
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            while chunk := content.read(8192):
                f.write(chunk)
        return str(full_path)

    async def get_path(self, path: str) -> str:
        return str(self._get_full_path(path))

    async def delete(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False
