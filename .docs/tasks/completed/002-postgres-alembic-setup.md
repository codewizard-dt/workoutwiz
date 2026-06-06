# 002 — Set Up PostgreSQL Database, Alembic Migrations, and Connection Pooling

> **Depends on**: [001-fastapi-project-structure](001-fastapi-project-structure.md)
> **Blocks**: [003-relational-schema-design](003-relational-schema-design.md)
> **Parallel-safe with**: [004-fastapi-logging-error-handling](004-fastapi-logging-error-handling.md)

## Objective

Configure a running PostgreSQL database for development, verify Alembic can connect and generate migrations, and tune async connection pooling on the SQLAlchemy engine created in TASK-001.

## Approach

- Use Docker Compose for a local PostgreSQL instance — no system-level Postgres install required
- Create the database, user, and password via Docker environment variables
- Tune `create_async_engine` pool settings (`pool_size`, `max_overflow`, `pool_pre_ping`)
- Generate an initial "empty" Alembic revision to confirm the migration pipeline works end-to-end

## Steps

### 1. Create docker-compose.yml for local development  <!-- agent: general-purpose -->

Create `docker-compose.yml` at the project root:

```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: workoutwiz
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

- [x] `docker-compose.yml` created at project root
- [x] `docker compose up -d db` starts PostgreSQL on port 5433 (5432 was occupied by another project; DATABASE_URL updated accordingly)
- [x] `docker compose ps` shows db service as healthy

---

### 2. Tune SQLAlchemy async engine pool settings  <!-- agent: general-purpose -->

Update `backend/app/database.py` to add pool configuration to the `create_async_engine` call:

```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
```

- [x] `backend/app/database.py` updated with pool settings
- [x] `pool_pre_ping=True` enabled (drops stale connections before use)

---

### 3. Run initial Alembic migration to confirm pipeline  <!-- agent: general-purpose -->

From `backend/`, with the database running:

1. Copy `.env.example` to `.env` and confirm `DATABASE_URL` points to the running container
2. Run `alembic revision --autogenerate -m "initial"` — should produce an empty migration (no tables yet)
3. Run `alembic upgrade head` — should succeed with no errors

- [x] `backend/.env` exists (copied from `.env.example`, not committed to git)
- [x] `backend/.gitignore` created (or updated) to exclude `.env`
- [x] `alembic revision --autogenerate -m "initial"` produces a file in `backend/migrations/versions/`
- [x] `alembic upgrade head` completes without errors
- [x] `alembic current` shows `head`

---

### 4. Verify async session dependency works  <!-- agent: general-purpose -->

Add a simple test route to `backend/app/main.py` to confirm the session dependency resolves:

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database import get_async_session

@app.get("/healthz/db")
async def db_health_check(session: AsyncSession = Depends(get_async_session)):
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
```

- [x] `GET /healthz/db` returns `{"status": "ok", "db": "connected"}` when DB is running
- [x] Remove this test route after verification (it's for smoke-testing only)

## Acceptance Criteria

- [x] `docker-compose.yml` starts a PostgreSQL 16 container on port 5433 (port 5432 was occupied)
- [x] SQLAlchemy engine uses async pool with `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`
- [x] Alembic can generate and apply migrations against the running database
- [x] `alembic upgrade head` and `alembic downgrade -1` both succeed
- [x] `.env` is excluded from git

---
**UAT**: [`.docs/uat/002-postgres-alembic-setup.uat.md`](../uat/002-postgres-alembic-setup.uat.md)
