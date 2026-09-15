"""Сервис работы с папками."""

import io
import uuid
import zipfile
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple

from fastapi.responses import StreamingResponse

from app.domain.entities.file import File
from app.domain.entities.folder import Folder
from app.domain.interfaces.file_repository import IFileRepository, IFileStorage
from app.domain.interfaces.folder_repository import IFolderRepository


class FolderService:
    """Сервис управления папками."""

    def __init__(
        self,
        folder_repository: IFolderRepository,
        file_repository: IFileRepository,
        file_storage: IFileStorage,
    ):
        self.folder_repository = folder_repository
        self.file_repository = file_repository
        self.file_storage = file_storage

    async def create_folder(self, name: str, owner_id: int, parent_id: Optional[int] = None) -> Optional[Folder]:
        """Создать папку."""
        if parent_id:
            parent = await self.folder_repository.get_by_id(parent_id)
            if not parent or parent.owner_id != owner_id:
                return None
        folder = Folder(id=None, name=name, owner_id=owner_id, parent_id=parent_id)
        return await self.folder_repository.create(folder)

    async def delete_folder(self, folder_id: int, user_id: int) -> bool:
        """Удалить папку (только владелец). Сначала удаляет файлы с диска."""
        folder = await self.folder_repository.get_by_id(folder_id)
        if not folder or folder.owner_id != user_id:
            return False
        # Удалить файлы с диска рекурсивно
        await self._delete_folder_files_from_storage(folder_id)
        return await self.folder_repository.delete(folder_id)

    async def _delete_folder_files_from_storage(self, folder_id: int):
        """Рекурсивно удалить файлы папки с диска."""
        files = await self.file_repository.get_by_folder(folder_id)
        for f in files:
            await self.file_storage.delete(f.storage_path)
        children = await self.folder_repository.get_children(folder_id)
        for child in children:
            await self._delete_folder_files_from_storage(child.id)

    async def get_folder_tree(self, owner_id: int, parent_id: Optional[int] = None) -> List[dict]:
        """Получить дерево папок и файлов."""
        result = []
        folders = await self.folder_repository.get_by_owner(owner_id, parent_id)
        files = await self.file_repository.get_by_owner_and_folder(owner_id, parent_id)

        for f in folders:
            result.append({
                "type": "folder",
                "id": f.id,
                "name": f.name,
                "parent_id": f.parent_id,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "children": await self.get_folder_tree(owner_id, f.id),
            })
        for f in files:
            result.append({
                "type": "file",
                "id": f.id,
                "name": f.original_filename,
                "size": f.size,
                "content_type": f.content_type,
                "folder_id": f.folder_id,
            })
        return result

    async def upload_folder(
        self,
        files_with_paths: List[Tuple[BinaryIO, str, int, str]],
        owner_id: int,
        parent_id: Optional[int] = None,
    ) -> List[File]:
        """
        Загрузить папку (несколько файлов с путями).
        files_with_paths: [(content, path, size, content_type), ...]
        path например "folder/sub/file.txt".
        parent_id — родительская папка, в которую загружается контент.
        """
        uploaded = []
        folder_cache: dict[str, int] = {}

        for content, path, size, content_type in files_with_paths:
            path_obj = Path(path)
            parts = path_obj.parts
            if len(parts) > 1:
                folder_id = await self._get_or_create_folder_path(
                    owner_id, list(parts[:-1]), folder_cache, root_parent_id=parent_id
                )
            else:
                folder_id = parent_id
            filename = parts[-1]
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
            created = await self.file_repository.create(file)
            uploaded.append(created)
        return uploaded

    async def _get_or_create_folder_path(
        self, owner_id: int, path_parts: List[str], cache: dict, root_parent_id: Optional[int] = None
    ) -> Optional[int]:
        if not path_parts:
            return root_parent_id
        key = "/".join(path_parts)
        if key in cache:
            return cache[key]
        parent_id = (
            await self._get_or_create_folder_path(owner_id, path_parts[:-1], cache, root_parent_id=root_parent_id)
            if len(path_parts) > 1
            else root_parent_id
        )
        folder = Folder(id=None, name=path_parts[-1], owner_id=owner_id, parent_id=parent_id)
        created = await self.folder_repository.create(folder)
        cache[key] = created.id
        return created.id

    async def download_folder_zip(self, folder_id: int, user_id: int) -> Optional[StreamingResponse]:
        """Скачать папку в виде ZIP-архива."""
        folder = await self.folder_repository.get_by_id(folder_id)
        if not folder or folder.owner_id != user_id:
            return None

        async def generate_zip():
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                await self._add_folder_to_zip(zf, folder_id, folder.name, "")
            buf.seek(0)
            data = buf.read()
            yield data

        return StreamingResponse(
            generate_zip(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{folder.name}.zip"'},
        )

    async def _add_folder_to_zip(
        self, zf: zipfile.ZipFile, folder_id: int, folder_name: str, prefix: str
    ):
        full_prefix = f"{prefix}{folder_name}/" if prefix or folder_name else ""
        files = await self.file_repository.get_by_folder(folder_id)
        for f in files:
            path = await self.file_storage.get_path(f.storage_path)
            zf.write(path, f"{full_prefix}{f.original_filename}")

        result = await self.folder_repository.get_children(folder_id)
        for child in result:
            await self._add_folder_to_zip(zf, child.id, child.name, full_prefix)
