"""Pydantic схемы для API."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Схема регистрации пользователя."""

    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Схема входа."""

    username: str
    password: str


class Token(BaseModel):
    """Схема токена."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""

    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """Схема ответа с данными файла."""

    id: int
    filename: str
    original_filename: str
    content_type: str
    size: int
    owner_id: int
    created_at: str | None

    class Config:
        from_attributes = True


class ShareRequest(BaseModel):
    """Схема запроса на шаринг."""

    shared_with_user_id: int
    permission: str = "read"
