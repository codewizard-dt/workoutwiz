# 006 — Implement /auth Endpoints with fastapi-users (register, signin, signout, token validation)

> **Depends on**: [003-relational-schema-design](003-relational-schema-design.md)
> **Blocks**: [008-workout-endpoints](008-workout-endpoints.md), [009-integration-tests](009-integration-tests.md)
> **Parallel-safe with**: [005-exercise-seed-data](005-exercise-seed-data.md), [007-exercise-endpoints](007-exercise-endpoints.md)

## Objective

Implement JWT-based authentication using `fastapi-users` (SQLAlchemy async backend). Expose `/auth/register`, `/auth/jwt/login`, `/auth/jwt/logout`, and a `/auth/me` endpoint. Add the `users` table via Alembic.

## Approach

- Use `fastapi-users` with `SQLAlchemyUserDatabase` — standard async SQLAlchemy adapter
- `User` model: UUID PK, email, hashed_password (all managed by fastapi-users)
- JWT transport with `BearerTransport` — no cookies
- `SECRET_KEY` from `settings.secret_key`
- Wire `fastapi-users` router to `/auth` prefix in `main.py`

## Steps

### 1. Create User model  <!-- agent: general-purpose -->

Create `backend/app/models/user.py`:

```python
import uuid
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass
```

Import in `backend/app/models/__init__.py`:
```python
from app.models.user import User
```

- [x] `backend/app/models/user.py` created extending `SQLAlchemyBaseUserTableUUID`
- [x] `User` imported in `app/models/__init__.py`

---

### 2. Generate and apply Alembic migration for users table  <!-- agent: general-purpose -->

With the `User` model registered to `Base.metadata`:

```bash
cd backend && alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

Also add the `user_id` foreign key constraint to `workouts` table in the same or a follow-on migration:

```python
# In the migration, add FK constraint to workouts.user_id
op.create_foreign_key("fk_workouts_user_id", "workouts", "users", ["user_id"], ["id"], ondelete="CASCADE")
```

- [x] Migration created adding `users` table (fastapi-users columns: id, email, hashed_password, is_active, is_superuser, is_verified)
- [x] `workouts.user_id` FK constraint added referencing `users.id` with CASCADE delete
- [x] `alembic upgrade head` succeeds

---

### 3. Create fastapi-users configuration  <!-- agent: general-purpose -->

Create `backend/app/auth.py`:

```python
import uuid
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database import get_async_session
from app.models.user import User
from app.config import settings


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=settings.access_token_expire_minutes * 60)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_db, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
```

- [x] `backend/app/auth.py` created with `fastapi_users` instance and `current_active_user` dependency
- [x] JWT strategy uses `settings.secret_key` and `settings.access_token_expire_minutes`

---

### 4. Create auth schemas  <!-- agent: general-purpose -->

Create `backend/app/schemas/user.py`:

```python
import uuid
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
```

- [x] `backend/app/schemas/user.py` created with `UserRead`, `UserCreate`, `UserUpdate`

---

### 5. Register auth routers in main.py  <!-- agent: general-purpose -->

In `backend/app/main.py`, import and include the fastapi-users routers:

```python
from app.auth import auth_backend, fastapi_users, current_active_user
from app.schemas.user import UserCreate, UserRead, UserUpdate

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

@app.get("/auth/me", tags=["auth"])
async def get_me(user=Depends(current_active_user)):
    return {"id": str(user.id), "email": user.email}
```

- [x] Auth routers included at `/auth/jwt` and `/auth`
- [x] `POST /auth/register` creates a new user
- [x] `POST /auth/jwt/login` returns a JWT token
- [x] `POST /auth/jwt/logout` invalidates the token (fastapi-users handles this)
- [x] `GET /auth/me` returns current user when authenticated; 401 when not

## Acceptance Criteria

- [x] `POST /auth/register` with valid email/password creates user and returns `UserRead`
- [x] `POST /auth/register` with duplicate email returns 400
- [x] `POST /auth/jwt/login` with valid credentials returns `{"access_token": "...", "token_type": "bearer"}`
- [x] `GET /auth/me` with valid token returns `{"id": "...", "email": "..."}`
- [x] `GET /auth/me` without token returns 401
- [x] Passwords are hashed (never stored in plaintext)
