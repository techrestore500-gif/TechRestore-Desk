from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Any


_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_actor_ctx: ContextVar[dict[str, Any] | None] = ContextVar("actor", default=None)


def set_request_id(request_id: str | None) -> Token:
    return _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def set_actor(actor: dict[str, Any] | None) -> Token:
    return _actor_ctx.set(actor)


def get_actor() -> dict[str, Any] | None:
    return _actor_ctx.get()


def reset_context(token: Token) -> None:
    token.var.reset(token)
