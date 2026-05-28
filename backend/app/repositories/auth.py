from __future__ import annotations

from app.database import get_connection, utc_now


class AuthRepository:
    @staticmethod
    def ensure_user_table() -> None:
        with get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL DEFAULT 'Tech Restore User',
                    email TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    approved_at TEXT,
                    approved_by INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "name" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN name TEXT")
                connection.execute("UPDATE users SET name = username WHERE name IS NULL OR TRIM(name) = ''")
            if "email" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN email TEXT")
                connection.execute("UPDATE users SET email = username || '@local.techrestore' WHERE email IS NULL OR TRIM(email) = ''")
            if "status" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN status TEXT")
                connection.execute("UPDATE users SET status = CASE WHEN is_active = 1 THEN 'active' ELSE 'disabled' END WHERE status IS NULL")
            if "approved_at" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN approved_at TEXT")
            if "approved_by" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN approved_by INTEGER")

            connection.execute("UPDATE users SET name = username WHERE name IS NULL OR TRIM(name) = ''")
            connection.execute("UPDATE users SET email = username || '@local.techrestore' WHERE email IS NULL OR TRIM(email) = ''")
            connection.execute("UPDATE users SET status = CASE WHEN is_active = 1 THEN 'active' ELSE 'disabled' END WHERE status IS NULL")
            connection.execute("UPDATE users SET approved_at = COALESCE(approved_at, created_at) WHERE status = 'active'")

            existing_indexes = {
                row["name"]
                for row in connection.execute("PRAGMA index_list(users)").fetchall()
            }
            if "idx_users_email_ci" not in existing_indexes:
                connection.execute("CREATE UNIQUE INDEX idx_users_email_ci ON users (LOWER(email))")
            connection.commit()

    @staticmethod
    def _select_user_base() -> str:
        return (
            "SELECT id, name, email, username, password_hash, role, status, is_active, approved_at, approved_by, created_at, updated_at "
            "FROM users"
        )

    @staticmethod
    def get_user_by_username(username: str) -> dict | None:
        return AuthRepository.get_user_by_identifier(username)

    @staticmethod
    def get_user_by_email(email: str) -> dict | None:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            row = connection.execute(
                f"{AuthRepository._select_user_base()} WHERE LOWER(email) = LOWER(?)",
                (email.strip(),),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_identifier(identifier: str) -> dict | None:
        AuthRepository.ensure_user_table()
        clean_identifier = identifier.strip()
        with get_connection() as connection:
            row = connection.execute(
                (
                    f"{AuthRepository._select_user_base()} "
                    "WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)"
                ),
                (clean_identifier, clean_identifier),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_id(user_id: int) -> dict | None:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            row = connection.execute(
                f"{AuthRepository._select_user_base()} WHERE id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def list_users() -> list[dict]:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            rows = connection.execute(
                f"{AuthRepository._select_user_base()} ORDER BY username ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def count_users() -> int:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"]) if row else 0

    @staticmethod
    def create_user(
        *,
        name: str,
        email: str,
        username: str,
        password_hash: str,
        role: str | None,
        status: str,
        approved_by: int | None,
    ) -> dict:
        AuthRepository.ensure_user_table()
        now = utc_now()
        approved_at = now if status == "active" else None
        is_active = 1 if status == "active" else 0
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    name,
                    email,
                    username,
                    password_hash,
                    role,
                    status,
                    is_active,
                    approved_at,
                    approved_by,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, email, username, password_hash, role, status, is_active, approved_at, approved_by, now, now),
            )
            connection.commit()

        created = AuthRepository.get_user_by_identifier(email)
        if created is None:
            raise ValueError("Failed to create user")
        return created

    @staticmethod
    def update_user_role(user_id: int, role: str) -> dict | None:
        AuthRepository.ensure_user_table()
        now = utc_now()
        with get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE users
                SET role = ?, updated_at = ?
                WHERE id = ?
                """,
                (role, now, user_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        return AuthRepository.get_user_by_id(user_id)

    @staticmethod
    def list_pending_requests() -> list[dict]:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            rows = connection.execute(
                f"{AuthRepository._select_user_base()} WHERE status = 'pending' ORDER BY created_at ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def set_user_status(
        *,
        user_id: int,
        status: str,
        role: str | None = None,
        approved_by: int | None = None,
    ) -> dict | None:
        AuthRepository.ensure_user_table()
        now = utc_now()
        is_active = 1 if status == "active" else 0
        with get_connection() as connection:
            current = connection.execute(
                f"{AuthRepository._select_user_base()} WHERE id = ?",
                (user_id,),
            ).fetchone()
            if current is None:
                return None

            next_role = role if role is not None else current["role"]
            next_approved_by = approved_by if status == "active" else current["approved_by"]
            next_approved_at = now if status == "active" else current["approved_at"]
            if status in {"denied", "disabled"}:
                next_approved_at = None
                next_approved_by = None
                if status == "denied":
                    next_role = None

            cursor = connection.execute(
                """
                UPDATE users
                SET role = ?, status = ?, is_active = ?, approved_at = ?, approved_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (next_role, status, is_active, next_approved_at, next_approved_by, now, user_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        return AuthRepository.get_user_by_id(user_id)
