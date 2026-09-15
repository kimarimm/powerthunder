"""Сервис аутентификации."""

import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.config import settings

# Настройки JWT
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


class AuthService:
    """Сервис аутентификации и авторизации."""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля."""
        try:
            pwd_bytes = plain_password.encode("utf-8")[:72]
            return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
        except (ValueError, UnicodeEncodeError):
            return False

    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля (bcrypt ограничен 72 байтами)."""
        pwd_bytes = password.encode("utf-8")[:72]
        return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Optional[dict]:
        """Декодирование JWT токена."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя."""
        user = await self.user_repository.get_by_username(username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
