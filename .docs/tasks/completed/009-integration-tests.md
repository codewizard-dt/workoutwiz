# 009 — Write Integration Tests for All Routes with Real Database

> **Depends on**: [006-auth-endpoints](006-auth-endpoints.md), [007-exercise-endpoints](007-exercise-endpoints.md), [008-workout-endpoints](008-workout-endpoints.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Write pytest integration tests for all API routes (`/auth`, `/exercises`, `/workouts`) that run against a real PostgreSQL test database (not mocked). Tests use `httpx.AsyncClient` with the FastAPI `app` and a test-scoped database with Alembic migrations applied fresh per test session.

## Approach

- Separate test database: `workoutwiz_test` (same host/credentials as dev DB)
- Session-scoped fixture: run Alembic migrations once at session start, drop all tables at session end
- Function-scoped fixture: wrap each test in a transaction and roll back after (fast cleanup)
- `httpx.AsyncClient` with `ASGITransport` — no real HTTP server needed
- Seed exercises once per session (same 50 records from exercises.json)

## Steps

### 1. Configure test database and pytest fixtures  <!-- agent: general-purpose -->

Create `backend/tests/__init__.py` (empty).

Create `backend/tests/conftest.py`:

```python
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from alembic import command
from alembic.config import Config
from app.main import app
from app.database import get_async_session, Base
from app.config import settings

TEST_DATABASE_URL = settings.database_url.replace("/workoutwiz", "/workoutwiz_test")

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations():
    """Run alembic upgrade head on the test DB once per session."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    yield
    # Teardown: drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_exercises(apply_migrations):
    """Seed exercises once per test session."""
    import json
    from pathlib import Path
    from app.schemas.exercise_seed import ExerciseSeedRecord

    data = json.loads((Path(__file__).parent.parent.parent / "1-multi-agent/exercises.json").read_text())
    records = [ExerciseSeedRecord(**e) for e in data]

    async with TestSessionLocal() as session:
        count = (await session.execute(text("SELECT COUNT(*) FROM exercises"))).scalar()
        if count == 0:
            for r in records:
                await session.execute(
                    text("INSERT INTO exercises VALUES (:id, :name, :category, :muscle_groups, :equipment_required, :movement_patterns::jsonb, :is_reps, :is_duration, :supports_weight, :is_bilateral, :bilateral_pair_id, :priority_tier, :description)"),
                    {**r.model_dump(), "id": str(r.id), "movement_patterns": __import__("json").dumps(r.movement_patterns), "bilateral_pair_id": str(r.bilateral_pair_id) if r.bilateral_pair_id else None},
                )
            await session.commit()


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    async with TestSessionLocal() as s:
        yield s


@pytest_asyncio.fixture
async def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_async_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

- [x] `backend/tests/__init__.py` created
- [x] `backend/tests/conftest.py` created with session-scoped migration fixture and function-scoped client fixture
- [x] Test database URL derived from `settings.database_url` (replaces DB name with `workoutwiz_test`)

---

### 2. Write auth endpoint tests  <!-- agent: general-purpose -->

Create `backend/tests/test_auth.py`:

Tests to cover:
- `POST /auth/register` with valid email/password → 201 (or 200) + user object
- `POST /auth/register` with duplicate email → 400
- `POST /auth/jwt/login` with valid credentials → `{"access_token": "...", "token_type": "bearer"}`
- `POST /auth/jwt/login` with wrong password → 400
- `GET /auth/me` with valid token → `{"id": "...", "email": "..."}`
- `GET /auth/me` without token → 401

Helper function `register_and_login(client, email, password) -> str` returns the token.

- [x] `backend/tests/test_auth.py` created
- [x] All 6 auth scenarios covered
- [x] `register_and_login` helper function extracted for reuse

---

### 3. Write exercise endpoint tests  <!-- agent: general-purpose -->

Create `backend/tests/test_exercises.py`:

Tests to cover:
- `GET /exercises` → 200, returns list of 50 exercises (no auth needed)
- `GET /exercises?name=squat` → returns exercises with "squat" in name
- `GET /exercises?muscle_groups=quadriceps` → returns exercises with that muscle group
- `GET /exercises?equipment=barbell` → returns exercises with barbell
- `GET /exercises?priority_tier=1` → returns only tier-1 exercises
- `GET /exercises?priority_tier=4` → 422 (priority_tier > 3 invalid)

- [x] `backend/tests/test_exercises.py` created
- [x] All 6 scenarios covered
- [x] Exercises test does not require auth

---

### 4. Write workout endpoint tests  <!-- agent: general-purpose -->

Create `backend/tests/test_workouts.py`:

Tests to cover:
- `GET /workouts` without auth → 401
- `POST /workouts` creates workout with sequences and sets → 201 + WorkoutRead
- `GET /workouts` returns only current user's workouts (not another user's)
- `GET /workouts/{id}` → 200 with nested sequences/sets
- `GET /workouts/{id}` for other user's workout → 404
- `PUT /workouts/{id}` replaces sequences → 200
- `DELETE /workouts/{id}` → 204; subsequent GET returns 404

Each test that needs a workout creates its own user + token first using `register_and_login`.

- [x] `backend/tests/test_workouts.py` created
- [x] All 7 scenarios covered
- [x] Cross-user isolation verified (user A cannot see user B's workouts)

---

### 5. Run full test suite  <!-- agent: general-purpose -->

From `backend/` with test database running:

```bash
pytest tests/ -v --tb=short
```

All tests must pass. Fix any failures before marking this task complete.

- [x] `pytest tests/ -v` exits with code 0
- [x] No skipped or xfailed tests (unless intentional)
- [x] Test output shows at least 19 tests passing

## Acceptance Criteria

- [x] Tests use real PostgreSQL (no mocks of the database layer)
- [x] Migrations applied once per session, exercises seeded once per session
- [x] Auth tests: register, login, me, duplicate-email, wrong-password, unauth
- [x] Exercise tests: list all, filter by name/muscle/equipment/tier, invalid tier
- [x] Workout tests: unauth, create, list isolation, get, cross-user 404, update, delete
- [x] `pytest tests/ -v` passes with 0 failures
