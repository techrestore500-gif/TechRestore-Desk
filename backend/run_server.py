from __future__ import annotations

import os

import uvicorn


def _resolve_host() -> str:
    app_env = (os.getenv("TECH_RESTORE_APP_ENV") or os.getenv("APP_ENV") or "development").strip().lower()
    if app_env == "development" and (os.getenv("RENDER") or "").strip().lower() == "true":
        app_env = "production"
    if app_env in {"production", "staging"}:
        return "0.0.0.0"
    return os.getenv("HOST", "127.0.0.1")


def _resolve_port() -> int:
    raw_port = os.getenv("PORT") or os.getenv("TECH_RESTORE_PORT") or "8787"
    try:
        return int(raw_port)
    except ValueError:
        return 8787


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=_resolve_host(), port=_resolve_port(), reload=False)
