from __future__ import annotations

import os
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.auth.dependencies import auth_enforcement_enabled
from app.core.request_context import reset_context, set_actor, set_request_id
from app.utils.jwt import decode_access_token


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        request.state.request_id = request_id

        request_id_token = set_request_id(request_id)
        actor_token = set_actor(_extract_actor_from_request(request))
        try:
            response: Response = await call_next(request)
        finally:
            reset_context(actor_token)
            reset_context(request_id_token)

        response.headers["X-Request-ID"] = request_id
        return response


def _extract_actor_from_request(request: Request) -> dict | None:
    if not auth_enforcement_enabled():
        return {
            "id": 0,
            "username": "dev-bypass",
            "role": "admin",
        }

    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None

    try:
        payload = decode_access_token(token)
    except Exception:
        return None

    uid = payload.get("uid")
    if not isinstance(uid, int):
        return None

    return {
        "id": uid,
        "username": payload.get("sub"),
        "role": payload.get("role"),
    }
