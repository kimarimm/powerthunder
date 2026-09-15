"""Интерфейс репозитория папок."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.folder import Folder


class IFolderRepository(ABC):
    """Абстрактный репозиторий папок."""

    @abstractmethod
    async def get_by_id(self, folder_id: int) -> Optional[Folder]:
        """Получить папку по ID."""
        pass

    @abstractmethod
    async def get_by_owner(self, owner_id: int, parent_id: Optional[int] = None) -> List[Folder]:
        """Получить папки владельца (в корне или в parent_id)."""
        pass

    @abstractmethod
    async def create(self, folder: Folder) -> Folder:
        """Создать папку."""
        pass

    @abstractmethod
    async def get_children(self, parent_id: int) -> List[Folder]:
        """Получить дочерние папки."""
        pass

    @abstractmethod
    async def delete(self, folder_id: int) -> bool:
        """Удалить папку (каскадно - файлы и вложенные папки)."""
        pass
