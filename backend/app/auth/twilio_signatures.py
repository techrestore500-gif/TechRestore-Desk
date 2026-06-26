from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request
from twilio.request_validator import RequestValidator

from app.core.settings import get_settings
from app.services.twilio import TwilioService


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _signature_bypass_requested() -> bool:
    return _is_truthy(os.getenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS"))


def _build_validation_urls(request: Request) -> list[str]:
    path = request.url.path
    query = request.url.query

    urls: list[str] = []
    public_base_url = TwilioService.get_settings().get("public_webhook_base_url")
    if isinstance(public_base_url, str) and public_base_url.strip():
        canonical = f"{public_base_url.rstrip('/')}{path}"
        if query:
            canonical = f"{canonical}?{query}"
        urls.append(canonical)

    # Fallback for local/test environments without a configured public base URL.
    urls.append(str(request.url))

    deduped: list[str] = []
    for candidate in urls:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


async def _request_signature_params(request: Request) -> dict[str, Any]:
    if request.method.upper() in {"POST", "PUT", "PATCH"}:
        form = await request.form()
        params: dict[str, Any] = {}
        for key, value in form.multi_items():
            if hasattr(value, "filename"):
                continue
            params[key] = str(value)
        return params
    return {key: value for key, value in request.query_params.items()}


async def verify_twilio_webhook_signature(request: Request) -> None:
    settings = get_settings()
    app_env = settings.app_env.lower()

    if _signature_bypass_requested():
        if app_env in {"production", "staging"}:
            raise HTTPException(status_code=403, detail="Twilio signature bypass is not allowed in production/staging")
        return

    signature = request.headers.get("X-Twilio-Signature", "").strip()
    if not signature:
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    _, auth_token = TwilioService._get_credentials()
    if not auth_token:
        raise HTTPException(status_code=403, detail="Twilio signature validation is not configured")

    validator = RequestValidator(auth_token)
    params = await _request_signature_params(request)

    for candidate_url in _build_validation_urls(request):
        if validator.validate(candidate_url, params, signature):
            return

    raise HTTPException(status_code=403, detail="Invalid Twilio signature")
