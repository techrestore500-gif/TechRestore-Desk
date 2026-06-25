from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RoleName = Literal["owner", "admin", "manager", "technician", "front_desk", "viewer"]
UserStatus = Literal["pending", "active", "denied", "disabled"]
InviteStatus = Literal["pending", "accepted", "revoked", "expired"]


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class AuthUserResponse(BaseModel):
    id: int
    name: str
    email: str = Field(min_length=3)
    username: str
    role: RoleName | None
    status: UserStatus
    is_active: bool
    created_at: str
    updated_at: str
    approved_at: str | None
    approved_by: int | None


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: AuthUserResponse


class AuthCreateUserRequest(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    role: RoleName


class AuthUpdateUserRoleRequest(BaseModel):
    role: RoleName


class AuthInviteCreateRequest(BaseModel):
    email: str = Field(min_length=3)
    name: str | None = None
    role: RoleName


class AuthInviteResponse(BaseModel):
    id: int
    email: str = Field(min_length=3)
    name: str | None
    role: RoleName
    status: InviteStatus
    expires_at: str
    created_at: str
    created_by: int | None
    accepted_at: str | None
    accepted_user_id: int | None
    revoked_at: str | None
    invite_link: str | None = None


class AuthInviteResolveResponse(BaseModel):
    email: str = Field(min_length=3)
    name: str | None
    role: RoleName
    expires_at: str


class AuthInviteAcceptRequest(BaseModel):
    password: str = Field(min_length=8)


class AuthDecisionResponse(BaseModel):
    message: str
    user: AuthUserResponse


class AuthChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


class AuthMessageResponse(BaseModel):
    message: str
