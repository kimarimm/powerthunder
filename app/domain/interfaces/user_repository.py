"""Интерфейс репозитория пользователей."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.user import User


class IUserRepository(ABC):
    """Абстрактный репозиторий пользователей."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по имени."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        """Создать пользователя."""
        pass
