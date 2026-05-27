from __future__ import annotations

from app.jobs.queue import list_dead_letters


class JobsRepository:
    @staticmethod
    def list_dead_letters(limit: int = 100) -> list[dict]:
        return list_dead_letters(limit=limit)
