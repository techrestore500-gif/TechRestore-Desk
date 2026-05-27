from __future__ import annotations

import json

from app.database import get_connection, row_to_dict, utc_now


class ActivityLogRepository:
    @staticmethod
    def create(
        *,
        user_id: int | None,
        entity_type: str,
        entity_id: int | None,
        action: str,
        old_value: dict | list | str | int | float | bool | None,
        new_value: dict | list | str | int | float | bool | None,
        request_id: str | None,
    ) -> dict:
        created_at = utc_now()
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO activity_logs (
                    user_id,
                    entity_type,
                    entity_id,
                    action,
                    old_value,
                    new_value,
                    request_id,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    entity_type,
                    entity_id,
                    action,
                    json.dumps(old_value) if old_value is not None else None,
                    json.dumps(new_value) if new_value is not None else None,
                    request_id,
                    created_at,
                ),
            )
            log_id = cursor.lastrowid
            connection.commit()

            row = connection.execute(
                "SELECT * FROM activity_logs WHERE id = ?",
                (log_id,),
            ).fetchone()

        result = row_to_dict(row)
        if result is None:
            raise RuntimeError("Failed to create activity log")

        for field in ("old_value", "new_value"):
            if result.get(field):
                result[field] = json.loads(result[field])
        return result

    @staticmethod
    def list_recent(limit: int = 100) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM activity_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            for field in ("old_value", "new_value"):
                if item.get(field):
                    item[field] = json.loads(item[field])
            items.append(item)
        return items

    @staticmethod
    def list_paginated(
        *,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> dict:
        page = max(1, page)
        page_size = max(1, min(500, page_size))
        offset = (page - 1) * page_size

        where_clauses = ["1=1"]
        params: list = []
        if action:
            where_clauses.append("action = ?")
            params.append(action)
        if entity_type:
            where_clauses.append("entity_type = ?")
            params.append(entity_type)
        where_sql = " AND ".join(where_clauses)

        with get_connection() as connection:
            total_row = connection.execute(
                f"SELECT COUNT(*) AS count FROM activity_logs WHERE {where_sql}",
                tuple(params),
            ).fetchone()

            rows = connection.execute(
                f"""
                SELECT * FROM activity_logs
                WHERE {where_sql}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [page_size, offset]),
            ).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            for field in ("old_value", "new_value"):
                if item.get(field):
                    item[field] = json.loads(item[field])
            items.append(item)

        total = int(total_row["count"]) if total_row else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
