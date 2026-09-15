"""Маршруты работы с папками."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.domain.entities.user import User
from app.application.services.folder_service import FolderService
from app.presentation.api.dependencies import get_folder_service, get_current_user

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.get("")
async def get_folder_tree(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    folder_service: Annotated[FolderService, Depends(get_folder_service)] = None,
):
    """Дерево папок и файлов пользователя."""
    tree = await folder_service.get_folder_tree(current_user.id, None)
    return {"items": tree}


@router.post("")
async def create_folder(
    name: str = Form(...),
    parent_id: int | None = Form(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    folder_service: Annotated[FolderService, Depends(get_folder_service)] = None,
):
    """Создать папку."""
    folder = await folder_service.create_folder(
        name=name, owner_id=current_user.id, parent_id=parent_id
    )
    if not folder:
        raise HTTPException(status_code=400, detail="Не удалось создать папку")
    return {"id": folder.id, "name": folder.name, "parent_id": folder.parent_id}


@router.post("/upload")
async def upload_folder(
    files: list[UploadFile] = File(...),
    parent_id: int | None = Form(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    folder_service: Annotated[FolderService, Depends(get_folder_service)] = None,
):
    """Загрузить папку (несколько файлов с путями в filename)."""
    if not files:
        raise HTTPException(status_code=400, detail="Нет файлов для загрузки")

    files_with_paths = []
    for f in files:
        path = f.filename or "unnamed"
        content = await f.read()
        size = len(content)
        from io import BytesIO

        files_with_paths.append(
            (BytesIO(content), path.replace("\\", "/"), size, f.content_type or "application/octet-stream")
        )

    uploaded = await folder_service.upload_folder(files_with_paths, current_user.id, parent_id=parent_id)
    return {"uploaded": len(uploaded), "files": [{"id": u.id, "name": u.original_filename} for u in uploaded]}


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    folder_service: Annotated[FolderService, Depends(get_folder_service)],
):
    """Удалить папку."""
    ok = await folder_service.delete_folder(folder_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Папка не найдена или удаление запрещено")
    return {"status": "ok"}


@router.get("/{folder_id}/download")
async def download_folder_zip(
    folder_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    folder_service: Annotated[FolderService, Depends(get_folder_service)],
):
    """Скачать папку в виде ZIP-архива."""
    response = await folder_service.download_folder_zip(folder_id, current_user.id)
    if not response:
        raise HTTPException(status_code=404, detail="Папка не найдена или доступ запрещён")
    return response
