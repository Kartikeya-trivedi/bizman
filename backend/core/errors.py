"""
BizMind AI — Error Handling & Retry Utilities
Global exception handler + exponential backoff retry decorator.
"""
import asyncio
import functools
import time
from typing import Any, Callable, TypeVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.core.logging import get_logger

logger = get_logger("errors")

F = TypeVar("F", bound=Callable[..., Any])

LLM_FALLBACK = "I'm having trouble right now, please try again in a moment."


def retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Retry decorator with exponential backoff (1s, 2s, 4s).
    Works with both sync and async callables.
    """
    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        last_exc = exc
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "Retry attempt",
                            func=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error=str(exc),
                        )
                        if attempt < max_attempts:
                            await asyncio.sleep(delay)
                raise last_exc  # type: ignore[misc]
            return async_wrapper  # type: ignore[return-value]
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as exc:
                        last_exc = exc
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "Retry attempt",
                            func=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=delay,
                            error=str(exc),
                        )
                        if attempt < max_attempts:
                            time.sleep(delay)
                raise last_exc  # type: ignore[misc]
            return sync_wrapper  # type: ignore[return-value]
    return decorator


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            endpoint=str(request.url),
            method=request.method,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc) if app.debug else "An internal error occurred.",
                "code": type(exc).__name__,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": str(exc), "code": "ValidationError"},
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": str(exc), "code": "PermissionDenied"},
        )
