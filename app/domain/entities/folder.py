"""Сущность папки."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Folder:
    """Доменная сущность папки."""

    id: Optional[int]
    name: str
    owner_id: int
    parent_id: Optional[int]
    created_at: Optional[datetime] = None
