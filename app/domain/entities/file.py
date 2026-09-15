"""Сущности файла и общего доступа."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class File:
    """Доменная сущность файла."""

    id: Optional[int]
    filename: str
    original_filename: str
    content_type: str
    size: int
    owner_id: int
    storage_path: str
    folder_id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class FileShare:
    """Сущность общего доступа к файлу."""

    id: Optional[int]
    file_id: int
    shared_with_user_id: int
    permission: str  # "read" | "write"
    created_at: Optional[datetime] = None
