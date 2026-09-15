"""Маршруты аутентификации."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.domain.entities.user import User
from app.presentation.api.dependencies import get_auth_service, get_user_service, get_current_user
from app.presentation.api.schemas import UserCreate, UserLogin, Token, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Регистрация нового пользователя."""
    hashed = auth_service.get_password_hash(data.password)
    user = await user_service.register(data.username, data.email, hashed)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем или email уже существует",
        )
    return UserResponse(id=user.id, username=user.username, email=user.email)


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Вход в систему."""
    user = await auth_service.authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    token = auth_service.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30),
    )
    return Token(access_token=token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Обновить токен по текущему (валидному) токену."""
    token = auth_service.create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=30),
    )
    return Token(access_token=token)
