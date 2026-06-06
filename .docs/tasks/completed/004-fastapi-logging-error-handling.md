# 004 — Configure Logging, Error Handling, and Async Patterns for FastAPI

> **Depends on**: [001-fastapi-project-structure](001-fastapi-project-structure.md)
> **Blocks**: none
> **Parallel-safe with**: [002-postgres-alembic-setup](002-postgres-alembic-setup.md), [003-relational-schema-design](003-relational-schema-design.md)

## Objective

Add structured logging, global exception handlers, and consistent error response shapes to the FastAPI app. This task produces cross-cutting infrastructure that all route handlers in Phase 2 will rely on.

## Approach

- Python `logging` with a JSON-structured handler for production readability
- FastAPI `exception_handler` decorators for `HTTPException`, `RequestValidationError`, and uncaught `Exception`
- Consistent error envelope: `{"detail": "...", "code": "...", "status": 4xx/5xx}`
- Request ID middleware for traceability
- No third-party logging library — stdlib `logging` is sufficient for the assessment

## Steps

### 1. Create logging configuration module  <!-- agent: general-purpose -->

Create `backend/app/logging_config.py`:

```python
import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # Quieten noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

Update `backend/app/config.py` to add a `log_level` field:

```python
log_level: str = "INFO"
```

Call `configure_logging(settings.log_level)` in `backend/app/main.py` during lifespan startup.

- [x] `backend/app/logging_config.py` created
- [x] `settings.log_level` added to `Settings`
- [x] `configure_logging()` called at app startup

---

### 2. Create error response schema  <!-- agent: general-purpose -->

Create `backend/app/schemas/errors.py`:

```python
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str
    status: int
```

- [x] `backend/app/schemas/errors.py` created with `ErrorResponse` Pydantic model

---

### 3. Add global exception handlers  <!-- agent: general-purpose -->

Create `backend/app/exception_handlers.py`:

```python
import logging
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": "http_error", "status": exc.status_code},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc.errors()), "code": "validation_error", "status": 422},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error", "status": 500},
    )
```

Register handlers in `backend/app/main.py`:

```python
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.exception_handlers import http_exception_handler, validation_exception_handler, unhandled_exception_handler

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
```

- [x] `backend/app/exception_handlers.py` created with three handlers
- [x] All three handlers registered in `main.py`
- [x] `GET /nonexistent` returns `{"detail": "Not Found", "code": "http_error", "status": 404}`

---

### 4. Add request ID middleware  <!-- agent: general-purpose -->

Add middleware to `backend/app/main.py` that injects a `X-Request-ID` header into every response (using `uuid4` if none provided by client):

```python
import uuid as _uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(_uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)
```

- [x] Every response includes `X-Request-ID` header
- [x] If client sends `X-Request-ID`, it is echoed back unchanged

## Acceptance Criteria

- [x] App startup logs at INFO level with timestamp and module name
- [x] `GET /nonexistent` → 404 JSON with `{"detail": "...", "code": "http_error", "status": 404}`
- [x] Invalid request body → 422 JSON with `{"detail": "...", "code": "validation_error", "status": 422}`
- [x] Unhandled exceptions → 500 JSON (no stack trace in response body)
- [x] Every response includes `X-Request-ID` header
- [x] SQLAlchemy engine logs suppressed at WARNING level (no SQL noise in stdout)

---
**UAT**: [`.docs/uat/004-fastapi-logging-error-handling.uat.md`](../uat/004-fastapi-logging-error-handling.uat.md)
