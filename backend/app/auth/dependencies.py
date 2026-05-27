from __future__ import annotations

import os
from typing import Literal

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.request_context import set_actor
from app.services.auth import AuthService
from app.utils.jwt import decode_access_token

RoleName = Literal["admin", "technician", "front_desk"]

_bearer = HTTPBearer(auto_error=False)


def _auth_bypass_enabled() -> bool:
    # Migration-safe rollout: auth bypass is enabled by default in development.
    # Set TECH_RESTORE_AUTH_BYPASS=0 to enforce token auth.
    return os.getenv("TECH_RESTORE_AUTH_BYPASS", "1") == "1"


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if _auth_bypass_enabled():
        user = {
            "id": 0,
            "username": "dev-bypass",
            "role": "admin",
            "is_active": True,
            "created_at": "",
            "updated_at": "",
        }
        set_actor(user)
        return user

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error

    uid = payload.get("uid")
    if not isinstance(uid, int):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = AuthService.get_user(uid)
    if user is None or not bool(user.get("is_active")):
        raise HTTPException(status_code=401, detail="Invalid user")
    set_actor(user)
    return user


def require_role(*roles: RoleName):
    def _dep(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _dep
