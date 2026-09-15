"""
Точка входа приложения.
Серверная часть веб-приложения для хранения и обмена файлами.
Архитектура: Clean Architecture
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.infrastructure.config import settings
from app.infrastructure.database.session import init_db
from app.presentation.api.routes import auth, files, folders

# Директория для статики и шаблонов
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATIC_DIR = os.path.abspath(STATIC_DIR)
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске."""
    await init_db()
    yield
    # shutdown при необходимости


app = FastAPI(
    title="Файловое хранилище",
    description="Серверная часть веб-приложения для хранения и обмена файлами",
    version="1.0.0",
    lifespan=lifespan,
)

# API routes
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(folders.router)

# Статические файлы
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    """Главная страница - SPA."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "File Storage API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        http="h11",
    )
