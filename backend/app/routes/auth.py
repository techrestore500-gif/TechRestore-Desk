import os

from fastapi import APIRouter, Depends, Header, HTTPException

from app.auth.dependencies import get_current_user, require_role
from app.schemas.auth import (
    AuthChangePasswordRequest,
    AuthCreateUserRequest,
    AuthDecisionResponse,
    AuthInviteAcceptRequest,
    AuthInviteCreateRequest,
    AuthInviteResolveResponse,
    AuthInviteResponse,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthMessageResponse,
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
    requester: dict = Depends(require_role("owner")),
) -> AuthUserResponse:
    try:
        user = AuthService.create_user_as_actor(
            actor=requester,
            name=payload.name,
            email=payload.email,
            username=payload.username,
            password=payload.password,
            role=payload.role,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    user_payload = {k: v for k, v in user.items() if k != "password_hash"}
    return AuthUserResponse.model_validate(user_payload)


@router.get("/users", response_model=list[AuthUserResponse])
def get_users(_: dict = Depends(require_role("owner"))) -> list[AuthUserResponse]:
    users = AuthService.list_users()
    return [AuthUserResponse.model_validate({k: v for k, v in user.items() if k != "password_hash"}) for user in users]


@router.patch("/users/{user_id}/role", response_model=AuthUserResponse)
def patch_user_role(
    user_id: int,
    payload: AuthUpdateUserRoleRequest,
    requester: dict = Depends(require_role("owner")),
) -> AuthUserResponse:
    try:
        updated = AuthService.update_user_role_as_actor(actor=requester, user_id=user_id, role=payload.role)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthUserResponse.model_validate({k: v for k, v in updated.items() if k != "password_hash"})


@router.delete("/users/{user_id}", response_model=AuthMessageResponse)
def delete_user(
    user_id: int,
    requester: dict = Depends(require_role("owner")),
) -> AuthMessageResponse:
    try:
        deleted = AuthService.delete_user_as_actor(actor=requester, user_id=user_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if deleted is None:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthMessageResponse(message=f"User {deleted['email']} has been successfully deleted.")


@router.get("/me", response_model=AuthUserResponse)
def get_me(user: dict = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse.model_validate({k: v for k, v in user.items() if k != "password_hash"})


@router.post("/change-password", response_model=AuthMessageResponse)
def post_change_password(
    payload: AuthChangePasswordRequest,
    user: dict = Depends(get_current_user),
) -> AuthMessageResponse:
    if int(user.get("id", 0)) == 0:
        raise HTTPException(status_code=403, detail="Shared-password sessions cannot change password")

    try:
        AuthService.change_password(
            user_id=int(user["id"]),
            current_password=payload.current_password,
            new_password=payload.new_password,
            confirm_password=payload.confirm_password,
        )
    except ValueError as error:
        message = str(error)
        if message == "Current password is incorrect":
            raise HTTPException(status_code=400, detail=message) from error
        raise HTTPException(status_code=400, detail=message) from error

    return AuthMessageResponse(message="Password changed successfully. Please sign in again.")


@router.get("/invites", response_model=list[AuthInviteResponse])
def get_invites(requester: dict = Depends(require_role("owner", "admin"))) -> list[AuthInviteResponse]:
    invites = AuthService.list_invites_for_actor(actor=requester)
    return [AuthInviteResponse.model_validate(item) for item in invites]


@router.post("/invites", response_model=AuthInviteResponse, status_code=201)
def post_invite(
    payload: AuthInviteCreateRequest,
    requester: dict = Depends(require_role("owner", "admin")),
) -> AuthInviteResponse:
    try:
        invite, token = AuthService.create_invite_as_actor(
            actor=requester,
            email=payload.email,
            name=payload.name,
            role=payload.role,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        if str(error) == "Failed to deliver invite email":
            try:
                invite, token = AuthService.create_invite_as_actor(
                    actor=requester,
                    email=payload.email,
                    name=payload.name,
                    role=payload.role,
                    send_email=False,
                )
            except PermissionError as fallback_error:
                raise HTTPException(status_code=403, detail=str(fallback_error)) from fallback_error
            except ValueError as fallback_error:
                raise HTTPException(status_code=400, detail=str(fallback_error)) from fallback_error
            invite_link = f"{_desk_base_url()}/invite/{token}"
            return AuthInviteResponse.model_validate(
                {
                    **invite,
                    "invite_link": invite_link,
                }
            )
        raise HTTPException(status_code=400, detail=str(error)) from error

    return AuthInviteResponse.model_validate(invite)


def _desk_base_url() -> str:
    return (
        os.getenv("FRONTEND_BASE_URL", "").strip()
        or os.getenv("PUBLIC_BASE_URL", "").strip()
        or "https://desk.techrestoredesk.com"
    ).rstrip("/")


@router.post("/invites/{invite_id}/revoke", response_model=AuthInviteResponse)
def post_revoke_invite(invite_id: int, requester: dict = Depends(require_role("owner", "admin"))) -> AuthInviteResponse:
    try:
        updated = AuthService.revoke_invite_as_actor(actor=requester, invite_id=invite_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Invite not found or already finalized")
    return AuthInviteResponse.model_validate(updated)


@router.post("/invites/{invite_id}/resend", response_model=AuthInviteResponse)
def post_resend_invite(invite_id: int, requester: dict = Depends(require_role("owner", "admin"))) -> AuthInviteResponse:
    try:
        updated = AuthService.resend_invite_as_actor(actor=requester, invite_id=invite_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AuthInviteResponse.model_validate(updated)
