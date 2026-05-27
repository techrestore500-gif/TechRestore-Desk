from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def install_error_handlers(app: FastAPI, *, include_trace: bool = False) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, error: StarletteHTTPException):
        request_id = _request_id(request)
        logger.warning(
            "HTTP exception",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": error.status_code,
                "error_type": "http_exception",
            },
        )
        return JSONResponse(
            status_code=error.status_code,
            content={
                "detail": str(error.detail),
                "error": {
                    "code": "http_error",
                    "message": str(error.detail),
                },
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError):
        request_id = _request_id(request)
        details = jsonable_encoder(error.errors())
        logger.warning(
            "Validation error",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
                "error_type": "validation_error",
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed",
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": details,
                },
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, error: Exception):
        request_id = _request_id(request)
        logger.exception(
            "Unhandled exception",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "error_type": error.__class__.__name__,
            },
        )

        body: dict[str, object] = {
            "detail": "Internal server error",
            "error": {
                "code": "internal_server_error",
                "message": "Internal server error",
            },
            "request_id": request_id,
        }
        if include_trace:
            body["error"] = {
                **body["error"],
                "details": str(error),
            }

        return JSONResponse(status_code=500, content=body)
