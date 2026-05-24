import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import AppError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except AppError as error:
            logger.warning(
                "Application error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": error.status_code,
                    "error_code": error.code,
                },
            )
            return JSONResponse(
                status_code=error.status_code,
                content={"error": {"code": error.code, "message": error.message}},
            )
        except Exception:
            logger.exception("Unhandled API error")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_server_error",
                        "message": "An unexpected error occurred",
                    },
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = perf_counter()
        response = await call_next(request)
        logger.info(
            "HTTP request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round((perf_counter() - started_at) * 1000),
            },
        )
        return response


async def app_error_handler(request: Request, exception: Exception) -> JSONResponse:
    error = cast(AppError, exception)
    logger.warning(
        "Application error",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": error.status_code,
            "error_code": error.code,
        },
    )
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


async def validation_error_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    del exception
    logger.warning(
        "Request validation failed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": 422,
            "error_code": "validation_error",
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
            },
        },
    )


async def http_error_handler(request: Request, exception: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exception)
    logger.warning(
        "HTTP error",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": error.status_code,
            "error_code": "http_error",
        },
    )
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": "http_error", "message": str(error.detail)}},
    )
