from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
import re
import secrets
import hashlib

logger = logging.getLogger(__name__)

from app.repositories.auth import AuthRepository
from app.events.audit_events import admin_action
from app.services.audit import AuditService
from app.services.emailer import EmailDeliveryError, EmailService
from app.utils.jwt import create_access_token
from app.utils.passwords import hash_password, verify_password

ALLOWED_ROLES = {"owner", "admin", "technician", "front_desk", "viewer"}
ALLOWED_STATUSES = {"pending", "active", "denied", "disabled"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INVITE_TOKEN_BYTES = 32
INVITE_EXPIRY_HOURS = int(os.getenv("TECH_RESTORE_INVITE_EXPIRY_HOURS", "72"))
MIN_PASSWORD_LENGTH = 8


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(INVITE_TOKEN_BYTES)


def _invite_is_expired(expires_at: str) -> bool:
    try:
        parsed = datetime.fromisoformat(expires_at)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed <= _utc_now()
    except ValueError:
        return True


def _to_public_invite(invite: dict) -> dict:
    status = invite.get("status")
    if status == "pending" and _invite_is_expired(str(invite.get("expires_at") or "")):
        status = "expired"
    return {
        "id": invite["id"],
        "email": invite["email"],
        "name": invite.get("name"),
        "role": invite["role"],
        "status": status,
        "expires_at": invite["expires_at"],
        "created_at": invite["created_at"],
        "created_by": invite.get("created_by"),
        "accepted_at": invite.get("accepted_at"),
        "accepted_user_id": invite.get("accepted_user_id"),
        "revoked_at": invite.get("revoked_at"),
    }


def _log_login_failure(email: str, reason: str) -> None:
    """Log login failure with reason code. Never logs passwords, hashes, or full emails."""
    domain = email.split("@", 1)[-1] if "@" in email else "unknown"
    logger.warning("login_failed reason=%s email_domain=%s", reason, domain)


def _desk_base_url() -> str:
    return (
        os.getenv("FRONTEND_BASE_URL", "").strip()
        or os.getenv("PUBLIC_BASE_URL", "").strip()
        or "https://desk.techrestoredesk.com"
    ).rstrip("/")


def _invite_expiry_hours() -> int:
    raw = os.getenv("TECH_RESTORE_INVITE_EXPIRY_HOURS", str(INVITE_EXPIRY_HOURS)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = INVITE_EXPIRY_HOURS
    return max(1, value)


def _send_invite_email(*, email: str, name: str | None, token: str) -> None:
    invite_link = f"{_desk_base_url()}/invite/{token}"
    EmailService.send_invite_email(
        recipient_email=email,
        recipient_name=name,
        invite_link=invite_link,
        expires_in_hours=_invite_expiry_hours(),
    )


def _bootstrap_admin_invite_details() -> tuple[str, str, str]:
    admin_email_raw = os.getenv("ADMIN_EMAIL", "").strip()
    admin_name = os.getenv("ADMIN_NAME", "").strip() or "Tech Restore Admin"
    admin_role = os.getenv("ADMIN_INVITE_ROLE", "owner").strip().lower() or "owner"

    if not admin_email_raw:
        raise ValueError("ADMIN_EMAIL is not configured")

    admin_email = _validate_email(admin_email_raw)
    if admin_role not in {"owner", "admin"}:
        admin_role = "owner"

    return admin_email, admin_name, admin_role


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


def _validate_new_password(current_password: str, new_password: str, confirm_password: str) -> str:
    current = current_password.strip()
    next_password = new_password.strip()
    confirmation = confirm_password.strip()

    if not current:
        raise ValueError("Current password is required")
    if not next_password:
        raise ValueError("New password is required")
    if len(next_password) < MIN_PASSWORD_LENGTH:
        raise ValueError("New password must be at least 8 characters")
    if next_password == current:
        raise ValueError("New password must be different from your current password")
    if next_password != confirmation:
        raise ValueError("New password and confirm password do not match")

    return next_password


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
    def login(email: str, password: str) -> tuple[dict, str, object]:
        normalized_email = _validate_email(email)
        shared_password = os.getenv("REPAIR_DESK_PASSWORD", "").strip()
        shared_auth_enabled = os.getenv("REPAIR_DESK_AUTH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}

        # Always check per-user auth first. Shared-password is only a fallback when no
        # individual account exists for this email (e.g. before first invite is accepted).
        user = AuthRepository.get_user_by_email(normalized_email)
        if user is None:
            if shared_auth_enabled and shared_password and password == shared_password:
                subject = normalized_email.strip() or "shared-password-admin"
                token, expires_at = create_access_token(subject=subject, role="admin", user_id=0)
                now = _utc_now().isoformat()
                shared_user = {
                    "id": 0,
                    "name": "Shared Password Admin",
                    "email": normalized_email,
                    "username": subject,
                    "role": "admin",
                    "status": "active",
                    "is_active": True,
                    "approved_at": now,
                    "approved_by": None,
                    "created_at": now,
                    "updated_at": now,
                }
                return shared_user, token, expires_at
            _log_login_failure(normalized_email, "user_not_found")
            raise ValueError("Invalid credentials")

        status = _normalize_status(user)
        if status == "pending":
            _log_login_failure(normalized_email, "account_pending")
            raise ValueError("Account is pending approval")
        if status == "denied":
            _log_login_failure(normalized_email, "account_denied")
            raise ValueError("Account request was denied")
        if status == "disabled":
            _log_login_failure(normalized_email, "account_disabled")
            raise ValueError("Account is disabled")
        if not user.get("role"):
            _log_login_failure(normalized_email, "no_role_assigned")
            raise ValueError("Account role is not assigned")
        if not user.get("is_active"):
            _log_login_failure(normalized_email, "account_inactive")
            raise ValueError("Invalid credentials")

        if not verify_password(password, user["password_hash"]):
            _log_login_failure(normalized_email, "wrong_password")
            raise ValueError("Invalid credentials")

        token, expires_at = create_access_token(subject=user["username"], role=user["role"], user_id=user["id"])
        return user, token, expires_at

    @staticmethod
    def create_invite(*, email: str, role: str, created_by: int, name: str | None = None, send_email: bool = True) -> tuple[dict, str]:
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")

        clean_email = _validate_email(email)
        AuthRepository.revoke_pending_invites_for_email(clean_email)

        token = _generate_invite_token()
        token_hash = _hash_invite_token(token)
        expires_at = (_utc_now().replace(microsecond=0) + timedelta(hours=_invite_expiry_hours())).isoformat()
        invite = AuthRepository.create_invite(
            email=clean_email,
            name=name.strip() if isinstance(name, str) and name.strip() else None,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=created_by,
        )

        if send_email:
            try:
                _send_invite_email(email=invite["email"], name=invite.get("name"), token=token)
            except EmailDeliveryError as error:
                AuthRepository.revoke_invite(int(invite["id"]))
                raise ValueError(str(error)) from error

        AuditService.log_event(
            admin_action(
                entity_type="auth_invite",
                entity_id=invite["id"],
                action="admin_invite_created",
                old_value=None,
                new_value={
                    "email": invite["email"],
                    "role": invite["role"],
                    "expires_at": invite["expires_at"],
                },
            )
        )
        return _to_public_invite(invite), token

    @staticmethod
    def resend_invite(*, invite_id: int, requested_by: int) -> dict:
        invite = AuthRepository.get_invite_by_id(invite_id)
        if invite is None:
            raise ValueError("Invite not found")

        public_invite = _to_public_invite(invite)
        if public_invite["status"] in {"accepted", "revoked"}:
            raise ValueError("Invite is not available")

        replacement, _ = AuthService.create_invite(
            email=invite["email"],
            name=invite.get("name"),
            role=invite["role"],
            created_by=requested_by,
            send_email=True,
        )
        AuditService.log_event(
            admin_action(
                entity_type="auth_invite",
                entity_id=invite_id,
                action="admin_invite_resent",
                old_value={"status": public_invite["status"]},
                new_value={
                    "email": replacement["email"],
                    "role": replacement["role"],
                    "status": replacement["status"],
                },
            )
        )
        return replacement

    @staticmethod
    def list_invites() -> list[dict]:
        invites = AuthRepository.list_invites()
        return [_to_public_invite(item) for item in invites]

    @staticmethod
    def revoke_invite(invite_id: int) -> dict | None:
        updated = AuthRepository.revoke_invite(invite_id)
        if updated is not None:
            AuditService.log_event(
                admin_action(
                    entity_type="auth_invite",
                    entity_id=invite_id,
                    action="admin_invite_revoked",
                    old_value=None,
                    new_value={"status": updated["status"]},
                )
            )
            return _to_public_invite(updated)
        return None

    @staticmethod
    def resolve_invite(token: str) -> dict:
        token_hash = _hash_invite_token(token)
        invite = AuthRepository.get_invite_by_token_hash(token_hash)
        if invite is None:
            raise ValueError("Invite not found")
        public_invite = _to_public_invite(invite)
        if public_invite["status"] != "pending":
            raise ValueError("Invite is not available")
        return {
            "email": public_invite["email"],
            "name": public_invite["name"],
            "role": public_invite["role"],
            "expires_at": public_invite["expires_at"],
        }

    @staticmethod
    def accept_invite(token: str, password: str) -> dict:
        token_hash = _hash_invite_token(token)
        invite = AuthRepository.get_invite_by_token_hash(token_hash)
        if invite is None:
            raise ValueError("Invite not found")

        public_invite = _to_public_invite(invite)
        if public_invite["status"] == "expired":
            raise ValueError("Invite has expired")
        if public_invite["status"] != "pending":
            raise ValueError("Invite is not available")

        password_digest = hash_password(password)
        existing_user = AuthRepository.get_user_by_email(invite["email"])
        if existing_user is None:
            user = AuthRepository.create_user(
                name=(invite.get("name") or invite["email"].split("@", 1)[0]).strip(),
                email=invite["email"],
                username=_generate_unique_username(invite.get("name") or invite["email"], invite["email"]),
                password_hash=password_digest,
                role=invite["role"],
                status="active",
                approved_by=invite.get("created_by"),
            )
        else:
            user = AuthRepository.update_user_from_invite(
                user_id=int(existing_user["id"]),
                name=(invite.get("name") or existing_user.get("name") or invite["email"]).strip(),
                role=invite["role"],
                password_hash=password_digest,
                approved_by=invite.get("created_by"),
            )
            if user is None:
                raise ValueError("Could not activate user")

        accepted = AuthRepository.mark_invite_as_accepted(int(invite["id"]), int(user["id"]))
        if accepted is None:
            raise ValueError("Invite is not available")

        AuditService.log_event(
            admin_action(
                entity_type="auth_invite",
                entity_id=invite["id"],
                action="auth_invite_accepted",
                old_value=None,
                new_value={
                    "email": invite["email"],
                    "role": invite["role"],
                    "accepted_user_id": user["id"],
                },
            )
        )
        return user

    @staticmethod
    def ensure_bootstrap_admin_invite_from_env(*, send_email: bool = True) -> dict | None:
        bootstrap_enabled = os.getenv("ADMIN_INVITE_BOOTSTRAP", "false").strip().lower() in {"1", "true", "yes", "on"}
        if not bootstrap_enabled:
            return None

        if AuthRepository.count_users() > 0 or AuthRepository.count_active_admins() > 0:
            return None

        try:
            admin_email, admin_name, admin_role = _bootstrap_admin_invite_details()
        except ValueError:
            return None

        pending = [invite for invite in AuthService.list_invites() if invite["email"].lower() == admin_email and invite["status"] == "pending"]
        if pending:
            return pending[0]

        invite, _ = AuthService.create_invite(
            email=admin_email,
            name=admin_name,
            role=admin_role,
            created_by=0,
            send_email=send_email,
        )

        AuditService.log_event(
            admin_action(
                entity_type="auth_invite",
                entity_id=invite["id"],
                action="startup_bootstrap_owner_invite_created",
                old_value=None,
                new_value={
                    "email": invite["email"],
                    "role": invite["role"],
                    "expires_at": invite["expires_at"],
                    "email_sent": send_email,
                },
            )
        )
        return invite

    @staticmethod
    def resend_bootstrap_admin_invite_from_env() -> dict:
        bootstrap_enabled = os.getenv("ADMIN_INVITE_BOOTSTRAP", "false").strip().lower() in {"1", "true", "yes", "on"}
        if not bootstrap_enabled:
            raise ValueError("Bootstrap invites are disabled")

        if AuthRepository.count_users() > 0 or AuthRepository.count_active_admins() > 0:
            raise ValueError("Bootstrap invite resend is unavailable after account setup")

        admin_email, admin_name, admin_role = _bootstrap_admin_invite_details()
        AuthRepository.revoke_pending_invites_for_email(admin_email)
        invite, _ = AuthService.create_invite(
            email=admin_email,
            name=admin_name,
            role=admin_role,
            created_by=0,
            send_email=True,
        )
        AuditService.log_event(
            admin_action(
                entity_type="auth_invite",
                entity_id=invite["id"],
                action="startup_bootstrap_owner_invite_resent",
                old_value=None,
                new_value={
                    "email": invite["email"],
                    "role": invite["role"],
                    "expires_at": invite["expires_at"],
                },
            )
        )
        return invite

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

    @staticmethod
    def change_password(*, user_id: int, current_password: str, new_password: str, confirm_password: str) -> None:
        user = AuthRepository.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        if int(user.get("id", 0)) == 0:
            raise ValueError("Shared-password sessions cannot change password")

        normalized_new_password = _validate_new_password(current_password, new_password, confirm_password)
        if not verify_password(current_password, user["password_hash"]):
            raise ValueError("Current password is incorrect")

        next_hash = hash_password(normalized_new_password)
        updated = AuthRepository.update_user_password_hash(user_id=int(user["id"]), password_hash=next_hash)
        if updated is None:
            raise ValueError("Unable to change password")

        AuditService.log_event(
            admin_action(
                entity_type="user",
                entity_id=user_id,
                action="auth_password_changed",
                old_value=None,
                new_value={"password_changed": True},
            )
        )
