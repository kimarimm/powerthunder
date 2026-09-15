"""Реализация репозитория файлов."""

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.file import File, FileShare
from app.domain.interfaces.file_repository import IFileRepository
from app.infrastructure.database.models import FileModel, FileShareModel, FolderModel


class FileRepository(IFileRepository):
    """Репозиторий файлов (SQLAlchemy)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: FileModel) -> File:
        return File(
            id=model.id,
            filename=model.filename,
            original_filename=model.original_filename,
            content_type=model.content_type,
            size=model.size,
            owner_id=model.owner_id,
            storage_path=model.storage_path,
            folder_id=getattr(model, "folder_id", None),
            created_at=model.created_at,
        )

    async def get_by_id(self, file_id: int) -> Optional[File]:
        result = await self.session.execute(select(FileModel).where(FileModel.id == file_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_owner(self, owner_id: int) -> List[File]:
        result = await self.session.execute(select(FileModel).where(FileModel.owner_id == owner_id))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_owner_and_folder(self, owner_id: int, folder_id: Optional[int]) -> List[File]:
        q = select(FileModel).where(FileModel.owner_id == owner_id)
        if folder_id is None:
            q = q.where(FileModel.folder_id.is_(None))
        else:
            q = q.where(FileModel.folder_id == folder_id)
        result = await self.session.execute(q)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_folder(self, folder_id: int) -> List[File]:
        result = await self.session.execute(select(FileModel).where(FileModel.folder_id == folder_id))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_all_in_folder_tree(self, folder_id: int) -> List[File]:
        files = await self.get_by_folder(folder_id)
        result = await self.session.execute(
            select(FolderModel).where(FolderModel.parent_id == folder_id)
        )
        for child in result.scalars().all():
            files.extend(await self.get_all_in_folder_tree(child.id))
        return files

    async def get_shared_with_user(self, user_id: int) -> List[File]:
        result = await self.session.execute(
            select(FileModel)
            .join(FileShareModel, FileShareModel.file_id == FileModel.id)
            .where(FileShareModel.shared_with_user_id == user_id)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, file: File) -> File:
        model = FileModel(
            filename=file.filename,
            original_filename=file.original_filename,
            content_type=file.content_type,
            size=file.size,
            owner_id=file.owner_id,
            storage_path=file.storage_path,
            folder_id=file.folder_id,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, file_id: int) -> bool:
        await self.session.execute(delete(FileShareModel).where(FileShareModel.file_id == file_id))
        result = await self.session.execute(delete(FileModel).where(FileModel.id == file_id))
        return result.rowcount > 0

    async def create_share(self, share: FileShare) -> FileShare:
        model = FileShareModel(
            file_id=share.file_id,
            shared_with_user_id=share.shared_with_user_id,
            permission=share.permission,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return FileShare(
            id=model.id,
            file_id=model.file_id,
            shared_with_user_id=model.shared_with_user_id,
            permission=model.permission,
            created_at=model.created_at,
        )

    async def check_access(self, file_id: int, user_id: int) -> bool:
        file = await self.get_by_id(file_id)
        if not file:
            return False
        if file.owner_id == user_id:
            return True
        result = await self.session.execute(
            select(FileShareModel).where(
                FileShareModel.file_id == file_id,
                FileShareModel.shared_with_user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None
