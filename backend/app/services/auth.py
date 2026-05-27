from __future__ import annotations

from app.repositories.auth import AuthRepository
from app.events.audit_events import admin_action
from app.services.audit import AuditService
from app.utils.jwt import create_access_token
from app.utils.passwords import hash_password, verify_password

ALLOWED_ROLES = {"admin", "technician", "front_desk"}


class AuthService:
    @staticmethod
    def create_user(username: str, password: str, role: str) -> dict:
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")

        existing = AuthRepository.get_user_by_username(username)
        if existing is not None:
            raise ValueError("Username already exists")

        password_hash = hash_password(password)
        user = AuthRepository.create_user(username=username, password_hash=password_hash, role=role)
        AuditService.log_event(
            admin_action(
                entity_type="user",
                entity_id=user["id"],
                action="admin_user_created",
                old_value=None,
                new_value={"username": user["username"], "role": user["role"], "is_active": user["is_active"]},
            )
        )
        return user

    @staticmethod
    def login(username: str, password: str) -> tuple[dict, str, object]:
        user = AuthRepository.get_user_by_username(username)
        if user is None or not user.get("is_active"):
            raise ValueError("Invalid credentials")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid credentials")

        token, expires_at = create_access_token(subject=user["username"], role=user["role"], user_id=user["id"])
        return user, token, expires_at

    @staticmethod
    def get_user(user_id: int) -> dict | None:
        return AuthRepository.get_user_by_id(user_id)

    @staticmethod
    def list_users() -> list[dict]:
        return AuthRepository.list_users()

    @staticmethod
    def update_user_role(user_id: int, role: str) -> dict | None:
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")
        existing = AuthRepository.get_user_by_id(user_id)
        updated = AuthRepository.update_user_role(user_id=user_id, role=role)
        if updated is not None:
            AuditService.log_event(
                admin_action(
                    entity_type="user",
                    entity_id=user_id,
                    action="admin_user_role_updated",
                    old_value={"role": existing["role"] if existing else None},
                    new_value={"role": updated["role"]},
                )
            )
        return updated
