from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


RoleName = Literal["owner", "admin", "technician", "front_desk", "viewer"]
UserStatus = Literal["pending", "active", "denied", "disabled"]


class AuthLoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3)
    username: str | None = Field(default=None, min_length=3)
    password: str = Field(min_length=8)

    @model_validator(mode="after")
    def _ensure_identifier(self) -> "AuthLoginRequest":
        if not (self.identifier or self.username):
            raise ValueError("identifier is required")
        return self


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


class AuthSignupRequest(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class AuthSignupResponse(BaseModel):
    message: str


class AuthAccessRequestResponse(BaseModel):
    id: int
    name: str
    email: str = Field(min_length=3)
    username: str
    status: UserStatus
    created_at: str


class AuthApproveRequest(BaseModel):
    role: RoleName


class AuthDecisionResponse(BaseModel):
    message: str
    user: AuthUserResponse
