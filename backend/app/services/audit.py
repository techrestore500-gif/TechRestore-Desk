from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.core.request_context import get_actor, get_request_id
from app.events.audit_events import AuditLogEvent
from app.repositories.activity_log import ActivityLogRepository

_REDACTED = "***redacted***"
_REDACT_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "secret",
}
_MAX_ITEMS = 30
_MAX_STR_LENGTH = 400
_MAX_DEPTH = 4


def _sanitize(value: Any, depth: int = 0) -> Any:
    if depth > _MAX_DEPTH:
        return "<truncated-depth>"

    if value is None or isinstance(value, (int, float, bool)):
        return value

    if isinstance(value, str):
        return value if len(value) <= _MAX_STR_LENGTH else f"{value[:_MAX_STR_LENGTH]}...<truncated>"

    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        items = list(value.items())[:_MAX_ITEMS]
        for key, item in items:
            key_str = str(key)
            if key_str.lower() in _REDACT_KEYS:
                sanitized[key_str] = _REDACTED
            else:
                sanitized[key_str] = _sanitize(item, depth + 1)
        if len(value) > _MAX_ITEMS:
            sanitized["_truncated_keys"] = len(value) - _MAX_ITEMS
        return sanitized

    if isinstance(value, (list, tuple, set)):
        as_list = list(value)
        sanitized_list = [_sanitize(item, depth + 1) for item in as_list[:_MAX_ITEMS]]
        if len(as_list) > _MAX_ITEMS:
            sanitized_list.append(f"<truncated-items:{len(as_list) - _MAX_ITEMS}>")
        return sanitized_list

    return _sanitize(str(value), depth + 1)


class AuditService:
    @staticmethod
    def log_event(event: AuditLogEvent) -> dict:
        actor = get_actor() or {}
        user_id = event.user_id if event.user_id is not None else actor.get("id")
        request_id = event.request_id or get_request_id()

        try:
            return ActivityLogRepository.create(
                user_id=user_id,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                action=event.action,
                old_value=_sanitize(event.old_value),
                new_value=_sanitize(event.new_value),
                request_id=request_id,
            )
        except Exception:
            return {
                "id": None,
                "user_id": user_id,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "action": event.action,
                "old_value": _sanitize(event.old_value),
                "new_value": _sanitize(event.new_value),
                "request_id": request_id,
                "created_at": None,
                "audit_persisted": False,
            }

    @staticmethod
    def log(
        *,
        entity_type: str,
        action: str,
        entity_id: int | None = None,
        old_value: Any = None,
        new_value: Any = None,
        user_id: int | None = None,
        request_id: str | None = None,
    ) -> dict:
        event = AuditLogEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id,
            request_id=request_id,
        )
        return AuditService.log_event(event)

    @staticmethod
    def to_snapshot(payload: Any) -> dict:
        if hasattr(payload, "model_dump"):
            return _sanitize(payload.model_dump())
        if hasattr(payload, "dict"):
            return _sanitize(payload.dict())
        if hasattr(payload, "__dict__"):
            return _sanitize(asdict(payload) if hasattr(payload, "__dataclass_fields__") else payload.__dict__)
        if isinstance(payload, dict):
            return _sanitize(payload)
        return {"value": _sanitize(payload)}
