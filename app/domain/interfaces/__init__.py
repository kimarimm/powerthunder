"""Интерфейсы доменного слоя (порты)."""

from app.domain.interfaces.user_repository import IUserRepository
from app.domain.interfaces.file_repository import IFileRepository, IFileStorage

__all__ = ["IUserRepository", "IFileRepository", "IFileStorage"]
