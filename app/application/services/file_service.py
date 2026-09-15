"""Сервис работы с файлами."""

import uuid
from typing import BinaryIO, List, Optional

from app.domain.entities.file import File, FileShare
from app.domain.interfaces.file_repository import IFileRepository, IFileStorage


class FileService:
    """Сервис управления файлами и обменом."""

    def __init__(self, file_repository: IFileRepository, file_storage: IFileStorage):
        self.file_repository = file_repository
        self.file_storage = file_storage

    async def upload_file(
        self,
        filename: str,
        content_type: str,
        content: BinaryIO,
        size: int,
        owner_id: int,
        folder_id: Optional[int] = None,
    ) -> File:
        """Загрузка файла."""
        storage_path = f"{owner_id}/{uuid.uuid4().hex}_{filename}"
        await self.file_storage.save(storage_path, content, size)

        file = File(
            id=None,
            filename=filename,
            original_filename=filename,
            content_type=content_type,
            size=size,
            owner_id=owner_id,
            storage_path=storage_path,
            folder_id=folder_id,
        )
        return await self.file_repository.create(file)

    async def get_file(self, file_id: int, user_id: int) -> Optional[File]:
        """Получить файл с проверкой доступа."""
        has_access = await self.file_repository.check_access(file_id, user_id)
        if not has_access:
            return None
        return await self.file_repository.get_by_id(file_id)

    async def get_storage_path(self, file: File) -> str:
        """Получить путь к файлу в хранилище."""
        return await self.file_storage.get_path(file.storage_path)

    async def list_user_files(self, user_id: int) -> List[File]:
        """Список файлов пользователя (свои + расшаренные)."""
        own_files = await self.file_repository.get_by_owner(user_id)
        shared_files = await self.file_repository.get_shared_with_user(user_id)

        seen_ids = {f.id for f in own_files}
        for f in shared_files:
            if f.id not in seen_ids:
                own_files.append(f)
                seen_ids.add(f.id)

        return own_files

    async def delete_file(self, file_id: int, user_id: int) -> bool:
        """Удаление файла (только владелец)."""
        file = await self.file_repository.get_by_id(file_id)
        if not file or file.owner_id != user_id:
            return False

        await self.file_storage.delete(file.storage_path)
        return await self.file_repository.delete(file_id)

    async def share_file(self, file_id: int, owner_id: int, shared_with_user_id: int, permission: str) -> Optional[FileShare]:
        """Поделиться файлом с пользователем."""
        file = await self.file_repository.get_by_id(file_id)
        if not file or file.owner_id != owner_id:
            return None

        share = FileShare(
            id=None,
            file_id=file_id,
            shared_with_user_id=shared_with_user_id,
            permission=permission,
        )
        return await self.file_repository.create_share(share)
