from __future__ import annotations

import os
from datetime import UTC, datetime
import re

from app.repositories.auth import AuthRepository
from app.events.audit_events import admin_action
from app.services.audit import AuditService
from app.utils.jwt import create_access_token
from app.utils.passwords import hash_password, verify_password

ALLOWED_ROLES = {"owner", "admin", "technician", "front_desk", "viewer"}
ALLOWED_STATUSES = {"pending", "active", "denied", "disabled"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_status(user: dict) -> str:
    status = str(user.get("status") or "").strip().lower()
    if status in ALLOWED_STATUSES:
        return status
    return "active" if bool(user.get("is_active")) else "disabled"


def _build_username_seed(name: str, email: str) -> str:
    source = name.strip() or email.split("@", 1)[0]
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "", source.lower())
    return slug or "techrestore"


def _validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_RE.match(normalized):
        raise ValueError("Invalid email address")
    return normalized


def _generate_unique_username(name: str, email: str) -> str:
    seed = _build_username_seed(name, email)
    candidate = seed
    suffix = 1
    while AuthRepository.get_user_by_identifier(candidate) is not None:
        suffix += 1
        candidate = f"{seed}{suffix}"
    return candidate


class AuthService:
    @staticmethod
    def create_user(name: str, email: str, username: str, password: str, role: str) -> dict:
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")

        clean_email = _validate_email(email)

        existing_username = AuthRepository.get_user_by_identifier(username)
        if existing_username is not None:
            raise ValueError("Username already exists")

        existing_email = AuthRepository.get_user_by_email(clean_email)
        if existing_email is not None:
            raise ValueError("Email already exists")

        password_hash = hash_password(password)
        user = AuthRepository.create_user(
            name=name.strip(),
            email=clean_email,
            username=username.strip(),
            password_hash=password_hash,
            role=role,
            status="active",
            approved_by=None,
        )
        AuditService.log_event(
            admin_action(
                entity_type="user",
                entity_id=user["id"],
                action="admin_user_created",
                old_value=None,
                new_value={
                    "name": user["name"],
                    "email": user["email"],
                    "username": user["username"],
                    "role": user["role"],
                    "status": user["status"],
                },
            )
        )
        return user

    @staticmethod
    def login(identifier: str, password: str) -> tuple[dict, str, object]:
        shared_password = os.getenv("REPAIR_DESK_PASSWORD", "").strip()
        shared_auth_enabled = os.getenv("REPAIR_DESK_AUTH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}

        if shared_auth_enabled and shared_password:
            if password != shared_password:
                raise ValueError("Invalid credentials")

            subject = identifier.strip() or "shared-password-admin"
            token, expires_at = create_access_token(subject=subject, role="admin", user_id=0)
            now = datetime.now(UTC).isoformat()
            user = {
                "id": 0,
                "name": "Shared Password Admin",
                "email": "shared-password-admin@local.techrestore",
                "username": subject,
                "role": "admin",
                "status": "active",
                "is_active": True,
                "approved_at": now,
                "approved_by": None,
                "created_at": now,
                "updated_at": now,
            }
            return user, token, expires_at

        user = AuthRepository.get_user_by_identifier(identifier)
        if user is None:
            raise ValueError("Invalid credentials")

        status = _normalize_status(user)
        if status == "pending":
            raise ValueError("Account is pending approval")
        if status == "denied":
            raise ValueError("Account request was denied")
        if status == "disabled":
            raise ValueError("Account is disabled")
        if not user.get("role"):
            raise ValueError("Account role is not assigned")
        if not user.get("is_active"):
            raise ValueError("Invalid credentials")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid credentials")

        token, expires_at = create_access_token(subject=user["username"], role=user["role"], user_id=user["id"])
        return user, token, expires_at

    @staticmethod
    def signup_request(name: str, email: str, password: str) -> dict:
        clean_email = _validate_email(email)
        existing = AuthRepository.get_user_by_email(clean_email)
        if existing is not None and _normalize_status(existing) in {"pending", "active"}:
            raise ValueError("An account request already exists for this email")

        username = _generate_unique_username(name=name, email=clean_email)
        password_hash = hash_password(password)
        user = AuthRepository.create_user(
            name=name.strip(),
            email=clean_email,
            username=username,
            password_hash=password_hash,
            role=None,
            status="pending",
            approved_by=None,
        )
        AuditService.log_event(
            admin_action(
                entity_type="user",
                entity_id=user["id"],
                action="auth_signup_requested",
                old_value=None,
                new_value={
                    "name": user["name"],
                    "email": user["email"],
                    "username": user["username"],
                    "status": user["status"],
                },
            )
        )
        return user

    @staticmethod
    def list_pending_access_requests() -> list[dict]:
        return AuthRepository.list_pending_requests()

    @staticmethod
    def approve_access_request(user_id: int, role: str, approver_user_id: int) -> dict | None:
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")
        updated = AuthRepository.set_user_status(
            user_id=user_id,
            status="active",
            role=role,
            approved_by=approver_user_id,
        )
        if updated is not None:
            AuditService.log_event(
                admin_action(
                    entity_type="user",
                    entity_id=user_id,
                    action="admin_access_request_approved",
                    old_value={"status": "pending"},
                    new_value={
                        "status": updated["status"],
                        "role": updated["role"],
                        "approved_by": updated.get("approved_by"),
                    },
                )
            )
        return updated

    @staticmethod
    def deny_access_request(user_id: int, approver_user_id: int) -> dict | None:
        updated = AuthRepository.set_user_status(
            user_id=user_id,
            status="denied",
            role=None,
            approved_by=approver_user_id,
        )
        if updated is not None:
            AuditService.log_event(
                admin_action(
                    entity_type="user",
                    entity_id=user_id,
                    action="admin_access_request_denied",
                    old_value={"status": "pending"},
                    new_value={"status": updated["status"]},
                )
            )
        return updated

    @staticmethod
    def ensure_bootstrap_admin_from_env() -> dict | None:
        if AuthRepository.count_users() > 0:
            return None

        admin_email_raw = os.getenv("ADMIN_EMAIL", "").strip()
        admin_name = os.getenv("ADMIN_NAME", "").strip() or "Tech Restore Owner"
        admin_password = os.getenv("ADMIN_PASSWORD", "")
        if not admin_email_raw or not admin_password.strip():
            return None

        try:
            admin_email = _validate_email(admin_email_raw)
        except ValueError:
            return None

        admin_username = _build_username_seed(admin_name, admin_email)
        if AuthRepository.get_user_by_identifier(admin_username) is not None:
            admin_username = _generate_unique_username(admin_name, admin_email)

        password_hash = hash_password(admin_password)
        user = AuthRepository.create_user(
            name=admin_name,
            email=admin_email,
            username=admin_username,
            password_hash=password_hash,
            role="owner",
            status="active",
            approved_by=None,
        )
        AuditService.log_event(
            admin_action(
                entity_type="user",
                entity_id=user["id"],
                action="startup_bootstrap_owner_created",
                old_value=None,
                new_value={
                    "name": user["name"],
                    "email": user["email"],
                    "username": user["username"],
                    "role": user["role"],
                    "status": user["status"],
                },
            )
        )
        return user

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
