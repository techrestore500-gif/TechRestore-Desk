import os

from fastapi import APIRouter, Depends, Header, HTTPException

from app.auth.dependencies import get_current_user, require_role
from app.schemas.auth import (
    AuthCreateUserRequest,
    AuthDecisionResponse,
    AuthInviteAcceptRequest,
    AuthInviteCreateRequest,
    AuthInviteResolveResponse,
    AuthInviteResponse,
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
        user, token, expires_at = AuthService.login(payload.email, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    user_payload = {k: v for k, v in user.items() if k != "password_hash"}
    return AuthLoginResponse(
        access_token=token,
        expires_at=expires_at,
        user=AuthUserResponse.model_validate(user_payload),
    )


@router.get("/invites/{token}", response_model=AuthInviteResolveResponse)
def get_invite_by_token(token: str) -> AuthInviteResolveResponse:
    try:
        invite = AuthService.resolve_invite(token)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AuthInviteResolveResponse.model_validate(invite)


@router.post("/invites/{token}/accept", response_model=AuthDecisionResponse)
def post_accept_invite(token: str, payload: AuthInviteAcceptRequest) -> AuthDecisionResponse:
    try:
        user = AuthService.accept_invite(token, payload.password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AuthDecisionResponse(
        message="Invite accepted. Your account is active.",
        user=AuthUserResponse.model_validate({k: v for k, v in user.items() if k != "password_hash"}),
    )


@router.post("/bootstrap/resend", response_model=AuthInviteResponse)
def post_bootstrap_resend(x_bootstrap_key: str | None = Header(default=None, alias="X-Bootstrap-Key")) -> AuthInviteResponse:
    expected_key = os.getenv("ADMIN_INVITE_BOOTSTRAP_KEY", "").strip()
    if not expected_key:
        raise HTTPException(status_code=404, detail="Bootstrap resend endpoint disabled")
    if x_bootstrap_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        invite = AuthService.resend_bootstrap_admin_invite_from_env()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AuthInviteResponse.model_validate(invite)


@router.post("/users", response_model=AuthUserResponse, status_code=201)
def post_user(
    payload: AuthCreateUserRequest,
    _: dict = Depends(require_role("owner", "admin")),
) -> AuthUserResponse:
    try:
        user = AuthService.create_user(payload.name, payload.email, payload.username, payload.password, payload.role)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    user_payload = {k: v for k, v in user.items() if k != "password_hash"}
    return AuthUserResponse.model_validate(user_payload)


@router.get("/users", response_model=list[AuthUserResponse])
def get_users(_: dict = Depends(require_role("owner", "admin"))) -> list[AuthUserResponse]:
    users = AuthService.list_users()
    return [AuthUserResponse.model_validate({k: v for k, v in user.items() if k != "password_hash"}) for user in users]


@router.patch("/users/{user_id}/role", response_model=AuthUserResponse)
def patch_user_role(
    user_id: int,
    payload: AuthUpdateUserRoleRequest,
    _: dict = Depends(require_role("owner", "admin")),
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


@router.get("/invites", response_model=list[AuthInviteResponse])
def get_invites(_: dict = Depends(require_role("owner", "admin"))) -> list[AuthInviteResponse]:
    invites = AuthService.list_invites()
    return [AuthInviteResponse.model_validate(item) for item in invites]


@router.post("/invites", response_model=AuthInviteResponse, status_code=201)
def post_invite(
    payload: AuthInviteCreateRequest,
    requester: dict = Depends(require_role("owner", "admin")),
) -> AuthInviteResponse:
    try:
        invite, _ = AuthService.create_invite(
            email=payload.email,
            name=payload.name,
            role=payload.role,
            created_by=int(requester["id"]),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return AuthInviteResponse.model_validate(invite)


@router.post("/invites/{invite_id}/revoke", response_model=AuthInviteResponse)
def post_revoke_invite(invite_id: int, _: dict = Depends(require_role("owner", "admin"))) -> AuthInviteResponse:
    updated = AuthService.revoke_invite(invite_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Invite not found or already finalized")
    return AuthInviteResponse.model_validate(updated)


@router.post("/invites/{invite_id}/resend", response_model=AuthInviteResponse)
def post_resend_invite(invite_id: int, requester: dict = Depends(require_role("owner", "admin"))) -> AuthInviteResponse:
    try:
        updated = AuthService.resend_invite(invite_id=invite_id, requested_by=int(requester["id"]))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AuthInviteResponse.model_validate(updated)
