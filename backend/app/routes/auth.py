from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user, require_role
from app.schemas.auth import (
    AuthCreateUserRequest,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthUpdateUserRoleRequest,
    AuthUserResponse,
)
from app.services.auth import AuthService


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthLoginResponse)
def post_login(payload: AuthLoginRequest) -> AuthLoginResponse:
    try:
        user, token, expires_at = AuthService.login(payload.username, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    user_payload = {k: v for k, v in user.items() if k != "password_hash"}
    return AuthLoginResponse(
        access_token=token,
        expires_at=expires_at,
        user=AuthUserResponse.model_validate(user_payload),
    )


@router.post("/users", response_model=AuthUserResponse, status_code=201)
def post_user(
    payload: AuthCreateUserRequest,
    _: dict = Depends(require_role("admin")),
) -> AuthUserResponse:
    try:
        user = AuthService.create_user(payload.username, payload.password, payload.role)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    user_payload = {k: v for k, v in user.items() if k != "password_hash"}
    return AuthUserResponse.model_validate(user_payload)


@router.get("/users", response_model=list[AuthUserResponse])
def get_users(_: dict = Depends(require_role("admin"))) -> list[AuthUserResponse]:
    users = AuthService.list_users()
    return [AuthUserResponse.model_validate({k: v for k, v in user.items() if k != "password_hash"}) for user in users]


@router.patch("/users/{user_id}/role", response_model=AuthUserResponse)
def patch_user_role(
    user_id: int,
    payload: AuthUpdateUserRoleRequest,
    _: dict = Depends(require_role("admin")),
) -> AuthUserResponse:
    try:
        updated = AuthService.update_user_role(user_id=user_id, role=payload.role)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthUserResponse.model_validate({k: v for k, v in updated.items() if k != "password_hash"})


@router.get("/me", response_model=AuthUserResponse)
def get_me(user: dict = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse.model_validate({k: v for k, v in user.items() if k != "password_hash"})
