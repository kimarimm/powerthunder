"""Зависимости API."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.file_repository import FileRepository
from app.infrastructure.repositories.folder_repository import FolderRepository
from app.infrastructure.storage.file_storage import LocalFileStorage
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.application.services.file_service import FileService
from app.application.services.folder_service import FolderService
from app.domain.entities.user import User

security = HTTPBearer(auto_error=False)


async def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


async def get_file_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> FileRepository:
    return FileRepository(db)


async def get_folder_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> FolderRepository:
    return FolderRepository(db)


def get_file_storage() -> LocalFileStorage:
    return LocalFileStorage()


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repo)


async def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


async def get_file_service(
    file_repo: Annotated[FileRepository, Depends(get_file_repository)],
    storage: Annotated[LocalFileStorage, Depends(get_file_storage)],
) -> FileService:
    return FileService(file_repo, storage)


async def get_folder_service(
    folder_repo: Annotated[FolderRepository, Depends(get_folder_repository)],
    file_repo: Annotated[FileRepository, Depends(get_file_repository)],
    storage: Annotated[LocalFileStorage, Depends(get_file_storage)],
) -> FolderService:
    return FolderService(folder_repo, file_repo, storage)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
        )
    payload = auth_service.decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
        )
    user_id = int(payload["sub"])
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user
