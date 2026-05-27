from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RoleName = Literal["admin", "technician", "front_desk"]


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)


class AuthUserResponse(BaseModel):
    id: int
    username: str
    role: RoleName
    is_active: bool
    created_at: str
    updated_at: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: AuthUserResponse


class AuthCreateUserRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    role: RoleName


class AuthUpdateUserRoleRequest(BaseModel):
    role: RoleName
