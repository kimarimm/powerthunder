"""Сервис управления пользователями."""

from typing import Optional

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import IUserRepository


class UserService:
    """Сервис регистрации и управления пользователями."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def register(self, username: str, email: str, hashed_password: str) -> Optional[User]:
        """Регистрация нового пользователя."""
        if await self.user_repository.get_by_username(username):
            return None
        if await self.user_repository.get_by_email(email):
            return None

        user = User(
            id=None,
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
        return await self.user_repository.create(user)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        return await self.user_repository.get_by_id(user_id)
