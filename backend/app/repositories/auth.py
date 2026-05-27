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
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def get_user_by_username(username: str) -> dict | None:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, role, is_active, created_at, updated_at
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_id(user_id: int) -> dict | None:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, role, is_active, created_at, updated_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def list_users() -> list[dict]:
        AuthRepository.ensure_user_table()
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, username, password_hash, role, is_active, created_at, updated_at
                FROM users
                ORDER BY username ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def create_user(username: str, password_hash: str, role: str) -> dict:
        AuthRepository.ensure_user_table()
        now = utc_now()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (username, password_hash, role, now, now),
            )
            connection.commit()

        created = AuthRepository.get_user_by_username(username)
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
