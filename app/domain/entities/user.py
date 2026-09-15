"""Сущность пользователя."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Доменная сущность пользователя."""

    id: Optional[int]
    username: str
    email: str
    hashed_password: str
    created_at: Optional[datetime] = None
