from __future__ import annotations

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.auth.dependencies import auth_enforcement_enabled, authenticate_bearer_token


PUBLIC_API_PATHS = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/bootstrap/resend",
    "/api/twilio/voice",
    "/api/twilio/recording",
    "/api/market-updates/sms",
}


class AuthGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not auth_enforcement_enabled():
            return await call_next(request)

        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        is_public_invite_route = path.startswith("/api/auth/invites/") and (
            path.endswith("/accept") or path.count("/") == 4
        )

        if not path.startswith("/api") or path in PUBLIC_API_PATHS or is_public_invite_route:
            return await call_next(request)

        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

        token = authorization.split(" ", 1)[1].strip()
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

        try:
            user = authenticate_bearer_token(token)
        except HTTPException as error:
            return JSONResponse(status_code=error.status_code, content={"detail": error.detail})

        request.state.auth_user = user
        return await call_next(request)
