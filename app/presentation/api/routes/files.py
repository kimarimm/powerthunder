"""Маршруты работы с файлами."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse

from app.domain.entities.user import User
from app.application.services.file_service import FileService
from app.presentation.api.dependencies import get_file_service, get_current_user
from app.presentation.api.schemas import FileResponse as FileResponseSchema, ShareRequest

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("", response_model=list[FileResponseSchema])
async def list_files(
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
):
    """Список файлов пользователя."""
    files = await file_service.list_user_files(current_user.id)
    return [
        FileResponseSchema(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            content_type=f.content_type,
            size=f.size,
            owner_id=f.owner_id,
            created_at=f.created_at.isoformat() if f.created_at else None,
        )
        for f in files
    ]


@router.post("", response_model=FileResponseSchema)
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[int] = Form(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    file_service: Annotated[FileService, Depends(get_file_service)] = None,
):
    """Загрузка файла."""
    content = await file.read()
    size = len(content)
    from io import BytesIO

    f = await file_service.upload_file(
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        content=BytesIO(content),
        size=size,
        owner_id=current_user.id,
        folder_id=folder_id,
    )
    return FileResponseSchema(
        id=f.id,
        filename=f.filename,
        original_filename=f.original_filename,
        content_type=f.content_type,
        size=f.size,
        owner_id=f.owner_id,
        created_at=f.created_at.isoformat() if f.created_at else None,
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
):
    """Скачивание файла."""
    f = await file_service.get_file(file_id, current_user.id)
    if not f:
        raise HTTPException(status_code=404, detail="Файл не найден или доступ запрещён")
    path = await file_service.get_storage_path(f)
    return FileResponse(
        path=path,
        filename=f.original_filename,
        media_type=f.content_type,
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
):
    """Удаление файла."""
    ok = await file_service.delete_file(file_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Файл не найден или удаление запрещено")
    return {"status": "ok"}


@router.post("/{file_id}/share")
async def share_file(
    file_id: int,
    data: ShareRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
):
    """Поделиться файлом с пользователем."""
    share = await file_service.share_file(
        file_id=file_id,
        owner_id=current_user.id,
        shared_with_user_id=data.shared_with_user_id,
        permission=data.permission,
    )
    if not share:
        raise HTTPException(status_code=404, detail="Файл не найден или вы не владелец")
    return {"status": "ok", "share_id": share.id}
