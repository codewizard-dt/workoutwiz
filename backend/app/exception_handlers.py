import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request as StarletteRequest
import starlette.middleware.errors as _sme

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Patch ServerErrorMiddleware to not re-raise after calling the error handler.
# Starlette's default behaviour always re-raises so that test clients can
# optionally surface the original exception.  For in-process ASGI testing
# (httpx.AsyncClient + ASGITransport) this causes the exception to propagate
# out of the test rather than returning the 500 JSON response.  Removing the
# unconditional re-raise preserves the correct response-body behaviour while
# still delegating to the registered error handler for logging.
# ---------------------------------------------------------------------------

async def _patched_server_error_call(self, scope, receive, send):
    if scope["type"] != "http":
        await self.app(scope, receive, send)
        return

    response_started = False

    async def _send(message):
        nonlocal response_started
        if message["type"] == "http.response.start":
            response_started = True
        await send(message)

    try:
        await self.app(scope, receive, _send)
    except Exception as exc:
        request = StarletteRequest(scope)
        if self.debug:
            response = self.debug_response(request, exc)
        elif self.handler is None:
            response = self.error_response(request, exc)
        else:
            if is_async_callable(self.handler):
                response = await self.handler(request, exc)
            else:
                response = await run_in_threadpool(self.handler, request, exc)
        if not response_started:
            await response(scope, receive, send)
        # Do NOT re-raise: allow the 500 response to reach the caller cleanly.


_sme.ServerErrorMiddleware.__call__ = _patched_server_error_call


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
