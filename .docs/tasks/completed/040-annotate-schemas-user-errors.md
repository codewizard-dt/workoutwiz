# 040 — Annotate schemas/user.py and schemas/errors.py with OpenAPI Field metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md), [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md), [038-annotate-schemas-workout](038-annotate-schemas-workout.md), [039-annotate-schemas-chat](039-annotate-schemas-chat.md)

## Objective

Add `Field(description=..., example=...)` annotations to `UserRead`, `UserCreate` (in `backend/app/schemas/user.py`) and `ErrorResponse` (in `backend/app/schemas/errors.py`) so the Swagger UI shows rich documentation for auth and error responses.

## Approach

`ErrorResponse` is a plain Pydantic model — add `Field()` directly to its 3 fields.

`UserRead` and `UserCreate` are thin wrappers over `fastapi-users` base classes (`schemas.BaseUser[uuid.UUID]` and `schemas.BaseUserCreate`). Their bodies are currently `pass`. To add Field metadata without breaking fastapi-users' validation logic, re-declare each inherited field in the subclass body using `Field(description=..., example=...)`. Pydantic v2 allows field re-declaration in subclasses and uses the most-derived definition. The inherited fields for these bases are:

- `BaseUser[uuid.UUID]` → `id: UUID`, `email: str`, `is_active: bool`, `is_superuser: bool`, `is_verified: bool`
- `BaseUserCreate` → `email: str`, `password: str`

## Steps

### 1. Annotate ErrorResponse  <!-- agent: general-purpose -->

Edit `backend/app/schemas/errors.py`:

- Import `Field` from `pydantic`.
- Annotate the 3 fields in `ErrorResponse`:

| Field | Description | Example |
|-------|-------------|---------|
| `detail` | Human-readable error message | `"Resource not found"` |
| `code` | Machine-readable error code | `"NOT_FOUND"` |
| `status` | HTTP status code | `404` |

- [x] `Field` imported from `pydantic` <!-- Completed: 2026-06-06 -->
- [x] All 3 `ErrorResponse` fields have `description=` and `example=` <!-- Completed: 2026-06-06 -->
- [x] File is valid Python <!-- Completed: 2026-06-06 -->

### 2. Annotate UserRead  <!-- agent: general-purpose -->

Edit `backend/app/schemas/user.py`:

- Import `Field` from `pydantic` and `uuid` (likely already imported).
- In `UserRead`, replace `pass` with explicit field re-declarations:
  ```python
  class UserRead(schemas.BaseUser[uuid.UUID]):
      id: uuid.UUID = Field(description="Unique user identifier (UUID)", example="a1b2c3d4-e5f6-7890-abcd-ef1234567890")
      email: str = Field(description="User's email address", example="coach@example.com")
      is_active: bool = Field(description="Whether the account is active", example=True)
      is_superuser: bool = Field(description="Whether the user has superuser privileges", example=False)
      is_verified: bool = Field(description="Whether the email address has been verified", example=True)
  ```

- [x] `Field` imported in `user.py` <!-- Completed: 2026-06-06 -->
- [x] `UserRead` has all 5 inherited fields re-declared with `description=` and `example=` <!-- Completed: 2026-06-06 -->
- [x] `UserRead` no longer contains a bare `pass` <!-- Completed: 2026-06-06 -->
- [x] File is valid Python <!-- Completed: 2026-06-06 -->

### 3. Annotate UserCreate  <!-- agent: general-purpose -->

In `UserCreate` in `backend/app/schemas/user.py`, replace `pass` with:

```python
class UserCreate(schemas.BaseUserCreate):
    email: str = Field(description="Email address for the new account", example="coach@example.com")
    password: str = Field(description="Password for the new account (min 8 characters)", example="S3cur3P@ss!")
```

- [x] `UserCreate` has both inherited fields re-declared with `description=` and `example=` <!-- Completed: 2026-06-06 -->
- [x] `UserCreate` no longer contains a bare `pass` <!-- Completed: 2026-06-06 -->
- [x] File is valid Python <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/schemas/errors.py` has `Field` imports and all `ErrorResponse` fields annotated <!-- Completed: 2026-06-06 -->
- [x] `backend/app/schemas/user.py` has `Field` imports and both `UserRead` and `UserCreate` fields re-declared with descriptions <!-- Completed: 2026-06-06 -->
- [x] Running `python -c "from app.schemas.user import UserRead, UserCreate; from app.schemas.errors import ErrorResponse; print('OK')"` from `backend/` exits 0 <!-- Completed: 2026-06-06 -->
- [x] No existing tests broken (fastapi-users validation still works — field re-declaration is additive) <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/040-annotate-schemas-user-errors.uat.md`](../uat/040-annotate-schemas-user-errors.uat.md)
