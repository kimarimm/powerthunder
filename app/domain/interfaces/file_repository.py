"""Интерфейсы репозитория файлов и файлового хранилища."""

from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO

from app.domain.entities.file import File, FileShare


class IFileRepository(ABC):
    """Абстрактный репозиторий файлов."""

    @abstractmethod
    async def get_by_id(self, file_id: int) -> Optional[File]:
        """Получить файл по ID."""
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: int) -> List[File]:
        """Получить все файлы владельца."""
        pass

    @abstractmethod
    async def get_by_owner_and_folder(self, owner_id: int, folder_id: Optional[int]) -> List[File]:
        """Получить файлы владельца в папке (folder_id=None — в корне)."""
        pass

    @abstractmethod
    async def get_by_folder(self, folder_id: int) -> List[File]:
        """Получить файлы в папке."""
        pass

    @abstractmethod
    async def get_all_in_folder_tree(self, folder_id: int) -> List[File]:
        """Получить все файлы в папке и её подпапках (рекурсивно)."""
        pass

    @abstractmethod
    async def get_shared_with_user(self, user_id: int) -> List[File]:
        """Получить файлы, расшаренные с пользователем."""
        pass

    @abstractmethod
    async def create(self, file: File) -> File:
        """Создать запись о файле."""
        pass

    @abstractmethod
    async def delete(self, file_id: int) -> bool:
        """Удалить файл."""
        pass

    @abstractmethod
    async def create_share(self, share: FileShare) -> FileShare:
        """Создать общий доступ."""
        pass

    @abstractmethod
    async def check_access(self, file_id: int, user_id: int) -> bool:
        """Проверить доступ пользователя к файлу."""
        pass


class IFileStorage(ABC):
    """Абстрактное хранилище файлов."""

    @abstractmethod
    async def save(self, path: str, content: BinaryIO, size: int) -> str:
        """Сохранить файл."""
        pass

    @abstractmethod
    async def get_path(self, path: str) -> str:
        """Получить путь к файлу."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Удалить файл."""
        pass
