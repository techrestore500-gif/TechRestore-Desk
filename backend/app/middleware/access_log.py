from __future__ import annotations

import logging
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.request_context import get_actor, get_request_id

logger = logging.getLogger("app.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = perf_counter()
        response = await call_next(request)
        duration_ms = round((perf_counter() - start) * 1000, 2)

        actor = get_actor() or {}
        logger.info(
            "http_request",
            extra={
                "request_id": get_request_id() or getattr(request.state, "request_id", None),
                "user_id": actor.get("id"),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "action": "http_request",
            },
        )

        return response
