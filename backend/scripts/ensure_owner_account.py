from __future__ import annotations

import os
from dataclasses import dataclass

from app.database import DB_PATH, get_connection
from app.repositories.auth import AuthRepository
from app.utils.passwords import hash_password

DEFAULT_OWNER_EMAIL = "mattiskleinbh@gmail.com"
DEFAULT_OWNER_PASSWORD = "TR500tag"
DEFAULT_OWNER_NAME = "Mattis Klein"
DEFAULT_OWNER_USERNAME = "techrestoreowner"


@dataclass(frozen=True)
class OwnerSeedConfig:
    email: str
    password: str
    name: str
    username: str


@dataclass(frozen=True)
class OwnerSeedResult:
    action: str
    user_id: int
    masked_email: str


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _read_config_from_env() -> OwnerSeedConfig:
    email = _normalize_email(os.getenv("TECH_RESTORE_OWNER_EMAIL", DEFAULT_OWNER_EMAIL))
    password = os.getenv("TECH_RESTORE_OWNER_PASSWORD", DEFAULT_OWNER_PASSWORD).strip()
    name = os.getenv("TECH_RESTORE_OWNER_NAME", DEFAULT_OWNER_NAME).strip() or DEFAULT_OWNER_NAME
    username = os.getenv("TECH_RESTORE_OWNER_USERNAME", DEFAULT_OWNER_USERNAME).strip() or DEFAULT_OWNER_USERNAME

    if not email:
        raise ValueError("TECH_RESTORE_OWNER_EMAIL cannot be empty")
    if not password:
        raise ValueError("TECH_RESTORE_OWNER_PASSWORD cannot be empty")
    if not username:
        raise ValueError("TECH_RESTORE_OWNER_USERNAME cannot be empty")

    return OwnerSeedConfig(email=email, password=password, name=name, username=username)


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def ensure_owner_account(config: OwnerSeedConfig | None = None) -> OwnerSeedResult:
    resolved = config or _read_config_from_env()
    AuthRepository.ensure_user_table()

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id, email
            FROM users
            WHERE LOWER(email) = LOWER(?)
            LIMIT 1
            """,
            (resolved.email,),
        ).fetchone()

        password_digest = hash_password(resolved.password)

        if existing is None:
            username_conflict = connection.execute(
                """
                SELECT id, email
                FROM users
                WHERE LOWER(username) = LOWER(?)
                LIMIT 1
                """,
                (resolved.username,),
            ).fetchone()
            if username_conflict is not None:
                conflict_email = str(username_conflict["email"])
                raise ValueError(
                    "Configured username is already in use by a different account: "
                    f"{_mask_email(_normalize_email(conflict_email))}"
                )

            created = AuthRepository.create_user(
                name=resolved.name,
                email=resolved.email,
                username=resolved.username,
                password_hash=password_digest,
                role="owner",
                status="active",
                approved_by=None,
            )
            return OwnerSeedResult(
                action="created",
                user_id=int(created["id"]),
                masked_email=_mask_email(resolved.email),
            )

        user_id = int(existing["id"])
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?,
                role = 'owner',
                status = 'active',
                is_active = 1,
                approved_at = COALESCE(approved_at, created_at),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (password_digest, user_id),
        )
        connection.commit()
        return OwnerSeedResult(
            action="updated",
            user_id=user_id,
            masked_email=_mask_email(resolved.email),
        )


def main() -> int:
    result = ensure_owner_account()
    print(
        "owner account ensured "
        f"action={result.action} "
        f"email={result.masked_email} "
        f"user_id={result.user_id} "
        f"db_path={DB_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
