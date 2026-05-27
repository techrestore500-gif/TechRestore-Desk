from __future__ import annotations

import logging

from app.core.settings import Settings

logger = logging.getLogger(__name__)


def initialize_monitoring(settings: Settings) -> None:
    dsn = settings.sentry_dsn
    if not dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
    except Exception:
        logger.warning("Sentry SDK not available; skipping Sentry initialization")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[FastApiIntegration()],
    )
    logger.info("Sentry monitoring initialized", extra={"action": "sentry_initialized"})
