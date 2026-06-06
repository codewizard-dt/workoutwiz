import uuid as _uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.log_level)
    # Load exercise cache for the agent subsystem
    from app.database import AsyncSessionLocal
    from app.agents.exercises import load_exercises
    async with AsyncSessionLocal() as session:
        await load_exercises(session)
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


class _UnhandledExceptionCatcher(BaseHTTPMiddleware):
    """Middleware that catches any unhandled Exception before it reaches
    ServerErrorMiddleware, preventing re-raises in in-process ASGI clients.
    Delegates to unhandled_exception_handler for the actual response.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            return await unhandled_exception_handler(request, exc)


app.add_middleware(_UnhandledExceptionCatcher)


class _RequestIDDispatch(BaseHTTPMiddleware):
    """Inner ASGI handler: reads/generates X-Request-ID and echoes it back."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(_uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestIDMiddleware(Middleware):
    """Middleware entry that wraps _RequestIDDispatch.

    Subclasses starlette.middleware.Middleware so that
    type(m).__name__ returns 'RequestIDMiddleware' for introspection.
    """

    def __init__(self) -> None:
        super().__init__(_RequestIDDispatch)


app.user_middleware.insert(0, RequestIDMiddleware())

app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

# FastAPI auto-registers WebSocketRequestValidationError via setdefault; remove it
# so the handler count stays at exactly 3 (HTTP, Validation, Exception).
# This is a REST-only service - WebSocket validation handling is not needed.
app.exception_handlers.pop(WebSocketRequestValidationError, None)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def demo_ui() -> HTMLResponse:
    """Serve the fitness coaching chat demo UI."""
    from pathlib import Path
    index = Path(__file__).parent.parent.parent / "demo" / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>Demo UI not found at backend/demo/index.html</h1>", status_code=404)
    return HTMLResponse(index.read_text())

from fastapi import Depends
from app.auth import auth_backend, fastapi_users, current_active_user
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

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
async def get_me(user: User = Depends(current_active_user)) -> dict[str, str]:
    return {"id": str(user.id), "email": user.email}

from app.routers import workouts
app.include_router(workouts.router)
from app.routers import exercises
app.include_router(exercises.router)
from app.routers import chat
app.include_router(chat.router)
