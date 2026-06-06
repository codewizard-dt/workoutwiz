# 001 — Create FastAPI Project Structure

> **Depends on**: none
> **Blocks**: [002-postgres-alembic-setup](002-postgres-alembic-setup.md), [004-fastapi-logging-error-handling](004-fastapi-logging-error-handling.md)
> **Parallel-safe with**: none

## Objective

Scaffold the `backend/` directory with a production-ready FastAPI project: async SQLAlchemy engine, Pydantic Settings config, Alembic migrations wiring, and a runnable (empty) app. No routes or models yet — just the skeleton every subsequent task builds on.

## Approach

- Use `pyproject.toml` (not `requirements.txt`) for dependency management — standard for modern Python projects
- `pydantic-settings` for `.env` config (reads from `.env` file and environment variables)
- `sqlalchemy[asyncio]` + `asyncpg` for async PostgreSQL
- `fastapi-users[sqlalchemy]` pinned as a dependency (auth implementation is a later task)
- Alembic `env.py` wired to import SQLAlchemy Base so future migrations auto-detect models
- App lifespan context manager for startup/shutdown hooks (no deprecated `on_startup`)

## Steps

### 1. Create pyproject.toml and dependency manifest  <!-- agent: general-purpose -->

Create `backend/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "workoutwiz-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.1",
    "fastapi-users[sqlalchemy]>=13.0.0",
    "pydantic-settings>=2.2.1",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.6",
    "httpx>=0.27.0",
    "pytest-cov>=5.0.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [x] File created at `backend/pyproject.toml` <!-- Completed: 2026-06-04 -->

---

### 2. Create Pydantic Settings config  <!-- agent: general-purpose -->

Create `backend/app/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/workoutwiz"
    secret_key: str = "changeme-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
```

Create `backend/.env.example`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/workoutwiz
SECRET_KEY=changeme-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

- [x] `backend/app/config.py` created with `Settings` class and `settings` singleton <!-- Completed: 2026-06-04 -->
- [x] `backend/.env.example` created with all required fields <!-- Completed: 2026-06-04 -->

---

### 3. Create async SQLAlchemy database module  <!-- agent: general-purpose -->

Create `backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [x] `backend/app/database.py` created with `engine`, `AsyncSessionLocal`, `Base`, and `get_async_session` dependency <!-- Completed: 2026-06-04 -->
- [x] `Base` is `DeclarativeBase` subclass (SQLAlchemy 2.x style) <!-- Completed: 2026-06-04 -->

---

### 4. Create FastAPI app entry point  <!-- agent: general-purpose -->

Create `backend/app/main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connection pool opens automatically on first use
    yield
    # Shutdown: dispose engine
    from app.database import engine
    await engine.dispose()


app = FastAPI(title="Workout Wiz API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
```

- [x] `backend/app/main.py` created with `app` instance, CORS middleware, lifespan, and `/healthz` route <!-- Completed: 2026-06-04 -->
- [x] CORS allows `http://localhost:5173` (Vite dev default) <!-- Completed: 2026-06-04 -->

---

### 5. Create models and schemas package stubs  <!-- agent: general-purpose -->

Create the following empty `__init__.py` files to establish the package structure:

- `backend/app/__init__.py` — empty
- `backend/app/models/__init__.py` — empty
- `backend/app/schemas/__init__.py` — empty
- `backend/app/routers/__init__.py` — empty

- [x] All four `__init__.py` files created (may be empty) <!-- Completed: 2026-06-04 -->

---

### 6. Wire Alembic for async migrations  <!-- agent: general-purpose -->

Create `backend/alembic.ini` — standard Alembic config with `sqlalchemy.url` left as a placeholder (overridden in `env.py`):

Key line to set: `script_location = migrations`

Create `backend/migrations/env.py` — async-compatible Alembic env that:
1. Imports `settings` from `app.config` to get the DB URL at migration time
2. Imports `Base` from `app.database` so Alembic can see all models registered to it
3. Uses `run_async_migrations()` pattern (standard for asyncpg)

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base

# Alembic Config object
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn, target_metadata=target_metadata
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda _: context.run_migrations())
    await connectable.dispose()


def run_async_migrations() -> None:
    asyncio.run(run_migrations_online())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_async_migrations()
```

Create `backend/migrations/__init__.py` — empty.

- [x] `backend/alembic.ini` created with `script_location = migrations` <!-- Completed: 2026-06-04 -->
- [x] `backend/migrations/env.py` created with async migration support <!-- Completed: 2026-06-04 -->
- [x] `backend/migrations/__init__.py` created (empty) <!-- Completed: 2026-06-04 -->
- [x] Alembic reads DB URL from `app.config.settings` (no hardcoding) <!-- Completed: 2026-06-04 -->

---

### 7. Smoke test the project boots  <!-- agent: general-purpose -->

From `backend/`:
1. Install dependencies: `pip install -e ".[dev]"`
2. Confirm `uvicorn app.main:app --reload` starts without import errors (no DB needed for this)
3. Confirm `GET /healthz` returns `{"status": "ok"}`

- [x] `uvicorn app.main:app` starts without errors <!-- Completed: 2026-06-04 -->
- [x] `GET /healthz` returns `{"status": "ok"}` <!-- Completed: 2026-06-04 -->
- [x] No import errors in any created module <!-- Completed: 2026-06-04 -->

## Acceptance Criteria

- [x] `backend/pyproject.toml` exists with all listed dependencies pinned to minimum versions <!-- Completed: 2026-06-04 -->
- [x] `backend/app/config.py` exports a `settings` singleton; `Settings` reads from `.env` <!-- Completed: 2026-06-04 -->
- [x] `backend/app/database.py` exports `engine`, `AsyncSessionLocal`, `Base`, `get_async_session` <!-- Completed: 2026-06-04 -->
- [x] `backend/app/main.py` exports `app`; `/healthz` returns 200 <!-- Completed: 2026-06-04 -->
- [x] `backend/migrations/env.py` imports `Base.metadata` and uses async engine <!-- Completed: 2026-06-04 -->
- [x] No model or route logic in this task — stubs only <!-- Completed: 2026-06-04 -->
- [x] All files are importable without a running database <!-- Completed: 2026-06-04 -->

---
**UAT**: [`.docs/uat/completed/001-fastapi-project-structure.uat.md`](../uat/completed/001-fastapi-project-structure.uat.md)
