# UAT: Configure Logging, Error Handling, and Async Patterns for FastAPI

> **Source task**: [`.docs/tasks/004-fastapi-logging-error-handling.md`](../tasks/004-fastapi-logging-error-handling.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Working directory is `backend/` inside the project
- [ ] `.venv/bin/python` exists (virtualenv created and dependencies installed via `pip install -e ".[dev]"`)
- [ ] `backend/app/logging_config.py` exists
- [ ] `backend/app/schemas/errors.py` exists
- [ ] `backend/app/exception_handlers.py` exists
- [ ] `backend/app/main.py` exists
- [ ] `backend/app/config.py` exists

---

## Static / Import Tests

### UAT-STATIC-001: logging_config.py exists with configure_logging function

- **Description**: Verify `logging_config.py` is present and exports a callable `configure_logging` that accepts a `level` string parameter.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.logging_config import configure_logging; import inspect; sig = inspect.signature(configure_logging); print('OK params:', list(sig.parameters.keys()))"
  ```
- **Expected Result**: Exits 0 and prints `OK params: ['level']`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-002: ErrorResponse schema has required fields

- **Description**: Verify `backend/app/schemas/errors.py` contains `ErrorResponse` with `detail`, `code`, and `status` fields, all with the correct types.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.schemas.errors import ErrorResponse; m = ErrorResponse(detail='test', code='err', status=400); print('detail:', m.detail, '| code:', m.code, '| status:', m.status)"
  ```
- **Expected Result**: Exits 0 and prints `detail: test | code: err | status: 400`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-003: exception_handlers.py exports all three handlers

- **Description**: Verify `backend/app/exception_handlers.py` exports `http_exception_handler`, `validation_exception_handler`, and `unhandled_exception_handler`.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.exception_handlers import http_exception_handler, validation_exception_handler, unhandled_exception_handler; import asyncio; print('handlers:', http_exception_handler.__name__, validation_exception_handler.__name__, unhandled_exception_handler.__name__)"
  ```
- **Expected Result**: Exits 0 and prints `handlers: http_exception_handler validation_exception_handler unhandled_exception_handler`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-004: settings has log_level field with default INFO

- **Description**: Verify `backend/app/config.py` `Settings` class has a `log_level` field that defaults to `"INFO"`.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.config import Settings; s = Settings(); print('log_level:', s.log_level)"
  ```
- **Expected Result**: Exits 0 and prints `log_level: INFO`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-005: app.main imports without errors and registers all handlers and middleware

- **Description**: Verify `app.main` can be imported cleanly and that the app object has the three exception handlers and `RequestIDMiddleware` registered.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.main import app; handlers = list(app.exception_handlers.keys()); mw_names = [type(m).__name__ for m in app.user_middleware]; print('handlers:', len(handlers), '| middleware includes RequestIDMiddleware:', 'RequestIDMiddleware' in mw_names)"
  ```
- **Expected Result**: Exits 0 and prints `handlers: 3 | middleware includes RequestIDMiddleware: True`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-006: configure_logging callable does not raise on valid levels

- **Description**: Verify `configure_logging` executes without raising for standard log level strings.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "from app.logging_config import configure_logging; configure_logging('DEBUG'); configure_logging('INFO'); configure_logging('WARNING'); print('configure_logging OK for DEBUG/INFO/WARNING')"
  ```
- **Expected Result**: Exits 0 and prints `configure_logging OK for DEBUG/INFO/WARNING`
- [x] Pass <!-- 2026-06-04 -->

---

## API Tests

> **Note**: Tests UAT-API-001 through UAT-API-004 require the FastAPI dev server running on port 8000. Start it with:
> `cd backend && .venv/bin/uvicorn app.main:app --port 8000 &`
> A database connection is **not** required — these routes do not touch the DB.

### UAT-API-001: GET /nonexistent returns 404 with structured error envelope

- **Description**: Verify that a request to an undefined route returns a 404 JSON response matching the error envelope shape `{"detail": "...", "code": "http_error", "status": 404}`.
- **Steps**:
  1. Ensure the dev server is running on port 8000
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -i 'http://localhost:8000/nonexistent'
  ```
- **Expected Result**: HTTP `404 Not Found` with JSON body `{"detail":"Not Found","code":"http_error","status":404}`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-002: Every response includes X-Request-ID header (server-generated)

- **Description**: Verify that when no `X-Request-ID` header is sent by the client, the server generates and returns one in the response.
- **Steps**:
  1. Ensure the dev server is running on port 8000
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -I 'http://localhost:8000/healthz'
  ```
- **Expected Result**: Response headers include `x-request-id: <uuid4-format-value>` (e.g. `x-request-id: 3fa85f64-5717-4562-b3fc-2c963f66afa6`). The value must be a non-empty string.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-003: X-Request-ID sent by client is echoed back unchanged

- **Description**: Verify that when the client provides `X-Request-ID: my-trace-id-123`, the server echoes the same value in the response header.
- **Steps**:
  1. Ensure the dev server is running on port 8000
  2. Run the command below
- **Command**:
  ```bash
  curl -sS -I 'http://localhost:8000/healthz' -H 'X-Request-ID: my-trace-id-123'
  ```
- **Expected Result**: Response headers include `x-request-id: my-trace-id-123` (exact match, not a generated UUID).
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-API-004: POST with invalid body returns 422 with validation_error code

- **Description**: Verify that sending a malformed JSON body to an endpoint that expects structured input returns 422 with `{"detail": "...", "code": "validation_error", "status": 422}`.
- **Steps**:
  1. Ensure the dev server is running on port 8000
  2. Run the command below — it sends an empty JSON object to the health endpoint which does not accept a body; to get a proper 422 we target any route that validates a request body. Since `/healthz` is a GET, use the app's OpenAPI-generated echo via a POST to a nonexistent body-accepting route, which will trigger the HTTPException path. Instead trigger validation by POSTing bad data to a schema-validated route. Because this task's scope only includes the infrastructure (no domain routes exist yet), send an invalid Content-Type to exercise the validation handler indirectly:
  3. The cleanest approach at this stage: spin up a minimal test app inline:
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from pydantic import BaseModel
from app.exception_handlers import http_exception_handler, validation_exception_handler, unhandled_exception_handler

class Body(BaseModel):
    name: str

test_app = FastAPI()
test_app.add_exception_handler(HTTPException, http_exception_handler)
test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
test_app.add_exception_handler(Exception, unhandled_exception_handler)

@test_app.post('/test')
async def test_route(body: Body):
    return body

async def run():
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url='http://test') as client:
        r = await client.post('/test', json={})
    print('status:', r.status_code, '| code:', r.json().get('code'), '| status_field:', r.json().get('status'))

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0 and prints `status: 422 | code: validation_error | status_field: 422`
- [x] Pass <!-- 2026-06-04 -->

---

## Edge Case Tests

### UAT-EDGE-001: Unhandled exception returns 500 with no stack trace in response body

- **Description**: Verify that when an unhandled `Exception` propagates to the global handler, the response body is `{"detail": "Internal server error", "code": "internal_error", "status": 500}` and contains no Python traceback.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.exception_handlers import http_exception_handler, validation_exception_handler, unhandled_exception_handler

test_app = FastAPI()
test_app.add_exception_handler(HTTPException, http_exception_handler)
test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
test_app.add_exception_handler(Exception, unhandled_exception_handler)

@test_app.get('/boom')
async def boom():
    raise RuntimeError('surprise')

async def run():
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url='http://test') as client:
        r = await client.get('/boom')
    body = r.json()
    has_traceback = 'Traceback' in str(body)
    print('status:', r.status_code, '| code:', body.get('code'), '| no_traceback:', not has_traceback)

asyncio.run(run())
"
  ```
- **Expected Result**: Exits 0 and prints `status: 500 | code: internal_error | no_traceback: True`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-002: configure_logging suppresses sqlalchemy.engine below WARNING

- **Description**: Verify that after `configure_logging()` is called, the `sqlalchemy.engine` logger's effective level is WARNING (30) or higher, meaning DEBUG/INFO SQL noise is suppressed.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "import logging; from app.logging_config import configure_logging; configure_logging('DEBUG'); lvl = logging.getLogger('sqlalchemy.engine').level; print('sqlalchemy.engine level:', lvl, '(WARNING=30, suppressed if >=30):', lvl >= 30)"
  ```
- **Expected Result**: Exits 0 and prints `sqlalchemy.engine level: 30 (WARNING=30, suppressed if >=30): True`
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-003: configure_logging suppresses uvicorn.access below WARNING

- **Description**: Verify that after `configure_logging()` is called, the `uvicorn.access` logger's effective level is WARNING (30) or higher.
- **Steps**:
  1. Run the command below from `backend/`
- **Command**:
  ```bash
  .venv/bin/python -c "import logging; from app.logging_config import configure_logging; configure_logging('DEBUG'); lvl = logging.getLogger('uvicorn.access').level; print('uvicorn.access level:', lvl, '(suppressed if >=30):', lvl >= 30)"
  ```
- **Expected Result**: Exits 0 and prints `uvicorn.access level: 30 (suppressed if >=30): True`
- [x] Pass <!-- 2026-06-04 -->
