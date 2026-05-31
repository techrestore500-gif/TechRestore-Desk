from __future__ import annotations

import os
from typing import Literal
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.request_context import set_actor
from app.services.auth import AuthService
from app.utils.jwt import decode_access_token

RoleName = Literal["owner", "admin", "technician", "front_desk", "viewer"]

_bearer = HTTPBearer(auto_error=False)


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _shared_password() -> str | None:
    value = os.getenv("REPAIR_DESK_PASSWORD")
    if value is None:
        return None
    value = value.strip()
    return value or None


def _shared_password_auth_enabled() -> bool:
    return _to_bool(os.getenv("REPAIR_DESK_AUTH_ENABLED"), default=False) and _shared_password() is not None


def _build_shared_user(subject: str = "shared-password-admin") -> dict:
    timestamp = datetime.now(UTC).isoformat()
    return {
        "id": 0,
        "name": "Shared Password Admin",
        "email": "shared-password-admin@local.techrestore",
        "username": subject,
        "role": "admin",
        "status": "active",
        "is_active": True,
        "approved_at": timestamp,
        "approved_by": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def _auth_bypass_enabled() -> bool:
    auth_enabled = os.getenv("REPAIR_DESK_AUTH_ENABLED")
    if auth_enabled is not None:
        is_enabled = _to_bool(auth_enabled)
        return not is_enabled

    # Migration-safe rollout: auth bypass is enabled by default in development.
    # Set TECH_RESTORE_AUTH_BYPASS=0 to enforce token auth.
    return os.getenv("TECH_RESTORE_AUTH_BYPASS", "1") == "1"


def auth_enforcement_enabled() -> bool:
    return not _auth_bypass_enabled()


def authenticate_bearer_token(token: str) -> dict:
    try:
        payload = decode_access_token(token)
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error

    uid = payload.get("uid")
    if not isinstance(uid, int):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if _shared_password_auth_enabled() and uid == 0:
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            subject = "shared-password-admin"
        user = _build_shared_user(subject=subject.strip())
        set_actor(user)
        return user

    user = AuthService.get_user(uid)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user")

    status = str(user.get("status") or "").strip().lower()
    if status in {"pending", "denied", "disabled"}:
        raise HTTPException(status_code=401, detail="Invalid user")
    if not bool(user.get("is_active")):
        raise HTTPException(status_code=401, detail="Invalid user")
    set_actor(user)
    return user


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if _auth_bypass_enabled():
        user = _build_shared_user(subject="dev-bypass")
        set_actor(user)
        return user

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authenticate_bearer_token(credentials.credentials)


def require_role(*roles: RoleName):
    def _dep(user: dict = Depends(get_current_user)) -> dict:
        current_role = user.get("role")
        if current_role == "owner" and "admin" in roles:
            return user
        if current_role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _dep
