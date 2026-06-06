# UAT: Annotate User and Error Schemas with OpenAPI Field Metadata

> **Source task**: [`.docs/tasks/040-annotate-schemas-user-errors.md`](../tasks/040-annotate-schemas-user-errors.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend dependencies installed (`pip install -e .` or `poetry install` from `backend/`)
- [ ] Backend server running on `http://localhost:8000` (`uvicorn app.main:app --reload` from `backend/`)
- [ ] Database is up and migrations have been applied

---

## API Tests

### UAT-API-001: All three schemas import cleanly

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify the primary acceptance criterion — all three annotated classes import without `ImportError` or `SyntaxError`. This is the exact check specified in the task.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.user import UserRead, UserCreate; from app.schemas.errors import ErrorResponse; print('OK')"
  ```
- **Expected Result**: Output is `OK` with exit code 0. No exceptions raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: ErrorResponse JSON schema has `description` on all 3 fields

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify `ErrorResponse.model_json_schema()` has a `description` key for `detail`, `code`, and `status`.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.errors import ErrorResponse; s = ErrorResponse.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'description' not in v]; print('Missing descriptions:', missing or 'NONE'); print('Fields:', list(props.keys()))"
  ```
- **Expected Result**: Output contains `Missing descriptions: NONE` and `Fields: ['detail', 'code', 'status']` (order may vary).
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: UserRead JSON schema has `description` on all 5 fields

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify `UserRead.model_json_schema()` has a `description` key for `id`, `email`, `is_active`, `is_superuser`, and `is_verified`. The re-declarations in the subclass override the bare fastapi-users base class fields.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.user import UserRead; s = UserRead.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'description' not in v]; print('Missing descriptions:', missing or 'NONE'); print('Field count:', len(props))"
  ```
- **Expected Result**: Output contains `Missing descriptions: NONE` and `Field count: 5`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: UserCreate JSON schema has `description` on both fields

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify `UserCreate.model_json_schema()` has a `description` key for `email` and `password`. The re-declarations override the bare fastapi-users base class fields.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.user import UserCreate; s = UserCreate.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'description' not in v]; print('Missing email/password:', missing or 'NONE'); print('email desc:', props.get('email', {}).get('description')); print('password desc:', props.get('password', {}).get('description'))"
  ```
- **Expected Result**: Output contains `Missing email/password: NONE`, `email desc: Email address for the new account`, and `password desc: Password for the new account (min 8 characters)`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-005: OpenAPI `/openapi.json` includes descriptions on `ErrorResponse`, `UserRead`, and `UserCreate` components

- **Endpoint**: `GET /openapi.json`
- **Description**: Verify the live OpenAPI spec includes `description` fields for properties on all three newly annotated schemas. This confirms Swagger UI will display the annotations end-to-end.
- **Steps**:
  1. Ensure the backend server is running
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '[.components.schemas | to_entries[] | select(.key | test("ErrorResponse|UserRead|UserCreate")) | {schema: .key, missing_desc: [.value.properties // {} | to_entries[] | select(.value | has("description") | not) | .key]}] | map(select(.missing_desc | length > 0))'
  ```
- **Expected Result**: `200 OK`. The jq output is `[]` (empty array) — every property on `ErrorResponse`, `UserRead`, and `UserCreate` has a `description` field in the live spec.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: POST /auth/register accepts a valid request and returns UserRead-shaped body

- **Endpoint**: `POST /auth/register`
- **Description**: Verify that the fastapi-users registration endpoint still works after field re-declaration — the `UserCreate` schema annotation is additive and must not break fastapi-users' validation or the `UserRead` response serialization.
- **Steps**:
  1. Run the curl command below as-is (uses a unique email to avoid conflict)
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/auth/register' -H 'Content-Type: application/json' -d '{"email":"uat040-test@example.com","password":"S3cur3P@ss!"}' | jq '{id, email, is_active, is_superuser, is_verified}'
  ```
- **Expected Result**: `201 Created`. Response body contains `id` (UUID string), `email` (`"uat040-test@example.com"`), `is_active` (`true`), `is_superuser` (`false`), `is_verified` (`false`). All five `UserRead` fields are present.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: fastapi-users `UserCreate` password validation still enforced after annotation

- **Scenario**: Verify that re-declaring `password` with `Field(description=..., examples=[...])` in `UserCreate` does not bypass fastapi-users' built-in password validation (minimum length / non-empty). The annotation must remain additive.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/auth/register' -H 'Content-Type: application/json' -d '{"email":"uat040-short-pw@example.com","password":"x"}' | jq '{status_or_detail: (.detail // .detail[0].msg)}'
  ```
- **Expected Result**: `400 Bad Request` or `422 Unprocessable Entity`. Response contains a validation error indicating the password is too short or invalid (not a `201 Created`).
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: fastapi-users `UserCreate` email validation still enforced after annotation

- **Scenario**: Verify that re-declaring `email` with `Field(description=..., examples=[...])` does not bypass email format validation. An invalid email must still be rejected.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/auth/register' -H 'Content-Type: application/json' -d '{"email":"not-an-email","password":"S3cur3P@ss!"}' | jq '.detail'
  ```
- **Expected Result**: `422 Unprocessable Entity` or `400 Bad Request`. Response body contains a validation error referencing the `email` field (not a `201 Created`).
- [x] Pass <!-- 2026-06-06 -->
