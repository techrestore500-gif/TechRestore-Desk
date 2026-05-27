from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from app.core.request_context import get_request_id
from app.database import get_connection, row_to_dict, utc_now

JobHandler = Callable[[dict[str, Any]], None]
logger = logging.getLogger(__name__)


class JobPriority(str, Enum):
    CRITICAL = "critical"
    DEFAULT = "default"
    LOW = "low"


@dataclass
class JobEnvelope:
    job_name: str
    payload: dict[str, Any]
    queue: JobPriority
    max_retries: int
    idempotency_key: str | None
    request_id: str | None
    attempt: int = 1


class InProcessJobQueue:
    def __init__(self) -> None:
        self._handlers: dict[str, JobHandler] = {}

    def register(self, job_name: str, handler: JobHandler) -> None:
        self._handlers[job_name] = handler

    def enqueue(
        self,
        *,
        job_name: str,
        payload: dict[str, Any],
        queue: JobPriority = JobPriority.DEFAULT,
        max_retries: int = 3,
        idempotency_key: str | None = None,
    ) -> dict:
        if idempotency_key and self._is_completed(idempotency_key):
            return {"queued": False, "reason": "idempotent_skip", "job_name": job_name}

        envelope = JobEnvelope(
            job_name=job_name,
            payload=payload,
            queue=queue,
            max_retries=max_retries,
            idempotency_key=idempotency_key,
            request_id=get_request_id(),
        )

        thread = threading.Thread(target=self._run_job, args=(envelope,), daemon=True)
        thread.start()
        return {"queued": True, "job_name": job_name, "queue": queue.value}

    def run_now(
        self,
        *,
        job_name: str,
        payload: dict[str, Any],
        queue: JobPriority = JobPriority.DEFAULT,
        max_retries: int = 3,
        idempotency_key: str | None = None,
    ) -> dict:
        envelope = JobEnvelope(
            job_name=job_name,
            payload=payload,
            queue=queue,
            max_retries=max_retries,
            idempotency_key=idempotency_key,
            request_id=get_request_id(),
        )
        return self._run_job(envelope)

    def _run_job(self, envelope: JobEnvelope) -> dict:
        handler = self._handlers.get(envelope.job_name)
        if handler is None:
            self._record_dead_letter(envelope, "No handler registered")
            return {"ok": False, "error": "No handler registered"}

        if envelope.idempotency_key and self._is_completed(envelope.idempotency_key):
            return {"ok": True, "status": "already_completed"}

        try:
            handler(envelope.payload)
            if envelope.idempotency_key:
                self._mark_completed(envelope.idempotency_key, envelope.job_name)
            return {"ok": True, "attempt": envelope.attempt}
        except Exception as error:
            logger.exception(
                "Job execution failed",
                extra={
                    "action": "job_execution_failed",
                    "request_id": envelope.request_id,
                    "entity_type": "job",
                    "entity_id": envelope.idempotency_key,
                },
            )
            if envelope.attempt < envelope.max_retries:
                retry_envelope = JobEnvelope(
                    job_name=envelope.job_name,
                    payload=envelope.payload,
                    queue=envelope.queue,
                    max_retries=envelope.max_retries,
                    idempotency_key=envelope.idempotency_key,
                    request_id=envelope.request_id,
                    attempt=envelope.attempt + 1,
                )
                return self._run_job(retry_envelope)

            self._record_dead_letter(envelope, str(error))
            return {"ok": False, "error": str(error), "attempt": envelope.attempt}

    def _is_completed(self, idempotency_key: str) -> bool:
        try:
            with get_connection() as connection:
                row = connection.execute(
                    "SELECT id FROM job_executions WHERE idempotency_key = ? AND status = 'completed'",
                    (idempotency_key,),
                ).fetchone()
            return row is not None
        except sqlite3.OperationalError:
            # During isolated tests, job tables may be intentionally absent.
            return False

    def _mark_completed(self, idempotency_key: str, job_name: str) -> None:
        now = utc_now()
        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO job_executions (idempotency_key, job_name, status, created_at, completed_at)
                    VALUES (?, ?, 'completed', ?, ?)
                    ON CONFLICT(idempotency_key)
                    DO UPDATE SET status = excluded.status, completed_at = excluded.completed_at
                    """,
                    (idempotency_key, job_name, now, now),
                )
                connection.commit()
        except sqlite3.OperationalError:
            return

    def _record_dead_letter(self, envelope: JobEnvelope, error_message: str) -> None:
        try:
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO job_dead_letters (
                        queue,
                        job_name,
                        payload_json,
                        attempts,
                        error_message,
                        request_id,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        envelope.queue.value,
                        envelope.job_name,
                        json.dumps(envelope.payload),
                        envelope.attempt,
                        error_message,
                        envelope.request_id,
                        utc_now(),
                    ),
                )
                connection.commit()
        except sqlite3.OperationalError:
            return


def list_dead_letters(limit: int = 100) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM job_dead_letters
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    items: list[dict] = []
    for row in rows:
        item = row_to_dict(row) or {}
        payload = item.get("payload_json")
        item["payload"] = json.loads(payload) if payload else None
        item.pop("payload_json", None)
        items.append(item)
    return items


job_queue = InProcessJobQueue()
