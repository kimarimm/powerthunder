"""Реализация репозитория папок."""

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.folder import Folder
from app.domain.interfaces.folder_repository import IFolderRepository
from app.infrastructure.database.models import FolderModel


class FolderRepository(IFolderRepository):
    """Репозиторий папок (SQLAlchemy)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: FolderModel) -> Folder:
        return Folder(
            id=model.id,
            name=model.name,
            owner_id=model.owner_id,
            parent_id=model.parent_id,
            created_at=model.created_at,
        )

    async def get_by_id(self, folder_id: int) -> Optional[Folder]:
        result = await self.session.execute(select(FolderModel).where(FolderModel.id == folder_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_owner(self, owner_id: int, parent_id: Optional[int] = None) -> List[Folder]:
        q = select(FolderModel).where(FolderModel.owner_id == owner_id)
        if parent_id is None:
            q = q.where(FolderModel.parent_id.is_(None))
        else:
            q = q.where(FolderModel.parent_id == parent_id)
        result = await self.session.execute(q)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_children(self, parent_id: int) -> List[Folder]:
        result = await self.session.execute(
            select(FolderModel).where(FolderModel.parent_id == parent_id)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, folder: Folder) -> Folder:
        model = FolderModel(
            name=folder.name,
            owner_id=folder.owner_id,
            parent_id=folder.parent_id,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, folder_id: int) -> bool:
        from app.infrastructure.database.models import FileModel, FileShareModel

        # 1. Рекурсивно удалить все дочерние папки
        for child in await self.get_children(folder_id):
            await self.delete(child.id)

        # 2. Удалить шаринги файлов в этой папке
        file_ids_result = await self.session.execute(
            select(FileModel.id).where(FileModel.folder_id == folder_id)
        )
        file_ids = [row[0] for row in file_ids_result.fetchall()]
        if file_ids:
            await self.session.execute(
                delete(FileShareModel).where(FileShareModel.file_id.in_(file_ids))
            )

        # 3. Удалить файлы в этой папке
        await self.session.execute(delete(FileModel).where(FileModel.folder_id == folder_id))

        # 4. Удалить саму папку
        result = await self.session.execute(delete(FolderModel).where(FolderModel.id == folder_id))
        return result.rowcount > 0
