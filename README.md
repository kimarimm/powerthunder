# Серверная часть веб-приложения для хранения и обмена файлами

Курсовая работа по дисциплине «Бэкенд-разработка».  
Архитектура: **Clean Architecture**.

## Технологии

- **Язык:** Python
- **Фреймворк:** FastAPI
- **БД:** SQLite (SQLAlchemy, async)
- **Аутентификация:** JWT, bcrypt
- **Фронтенд:** HTML5, CSS3, JavaScript (SPA)
- **Контейнеризация:** Docker, Docker Compose
- **CI/CD:** GitHub Actions (деплой по SSH)

## Структура проекта (Clean Architecture)

```
├── app/
│   ├── domain/              # Доменный слой
│   │   ├── entities/        # Сущности (User, File, FileShare)
│   │   └── interfaces/      # Порты (репозитории)
│   ├── application/         # Слой приложения
│   │   └── services/        # Use cases (AuthService, FileService, UserService)
│   ├── infrastructure/      # Инфраструктура
│   │   ├── database/        # Модели, сессия БД
│   │   ├── repositories/    # Реализации репозиториев
│   │   └── storage/         # Файловое хранилище
│   └── presentation/        # Слой представления
│       └── api/             # REST API, схемы
├── static/                  # Статика (фронтенд)
├── .github/workflows/       # CI/CD (деплой по SSH)
├── Dockerfile                # Образ приложения
├── docker-compose.yml        # Запуск в контейнере
├── main.py                  # Точка входа
└── requirements.txt
```

## Установка и запуск

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env на основе примера и задать свой SECRET_KEY
copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"  # вставить в SECRET_KEY

# Запуск
python main.py
# или
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Приложение: http://localhost:8000  
API документация: http://localhost:8000/docs

## Docker

```bash
# Создать .env на основе примера и задать свой SECRET_KEY
copy .env.example .env

# Собрать и запустить
docker compose up -d --build
```

Приложение: http://localhost:8080

Деплой на сервер по SSH автоматизирован через GitHub Actions —
см. `.github/workflows/deploy.yml`.

## API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /api/auth/register | Регистрация |
| POST | /api/auth/login | Вход (JWT) |
| GET | /api/files | Список файлов |
| POST | /api/files | Загрузка файла |
| GET | /api/files/{id}/download | Скачивание |
| DELETE | /api/files/{id} | Удаление |
| POST | /api/files/{id}/share | Шаринг файла |
| GET | /api/folders | Дерево папок и файлов |
| POST | /api/folders | Создать папку |
| POST | /api/folders/upload | Загрузить папку (multipart) |
| GET | /api/folders/{id}/download | Скачать папку как ZIP |

## Функциональность

- Регистрация и аутентификация пользователей
- Загрузка и скачивание файлов
- **Создание папок и загрузка папок**
- **Скачивание папок в виде ZIP-архива**
- Обмен файлами между пользователями (share)
- Межстраничная навигация (SPA)
- Современный UI (адаптивный, тёмная тема)

> **При обновлении:** при добавлении папок удалите `file_storage.db` для пересоздания схемы БД.
