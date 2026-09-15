"""Конфигурация приложения (загружается из .env)."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаемые из переменных окружения / .env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # JWT / аутентификация
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # База данных
    database_url: str = "sqlite+aiosqlite:///./file_storage.db"

    # Файловое хранилище
    storage_root: Optional[str] = None

    # Сервер
    host: str = "127.0.0.1"
    port: int = 8080
    reload: bool = True


settings = Settings()
