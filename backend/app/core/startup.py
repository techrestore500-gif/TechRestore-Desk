"""Application startup helpers."""
import logging
import os

from app.core.monitoring import initialize_monitoring
from app.core.settings import get_settings
from app.database import initialize_database
from app.events.subscribers import register_event_subscribers
from app.jobs.registry import register_job_handlers
from app.services.auth import AuthService

logger = logging.getLogger(__name__)


def _is_set(name: str) -> bool:
    value = os.getenv(name)
    return value is not None and bool(value.strip())


def _log_production_env_warnings() -> None:
    required_any = {
        "SECRET_KEY": ["SECRET_KEY", "TECH_RESTORE_JWT_SECRET"],
        "DATABASE_URL": ["DATABASE_URL"],
        "FRONTEND_BASE_URL": ["FRONTEND_BASE_URL", "PUBLIC_BASE_URL"],
        "PUBLIC_API_BASE_URL": ["PUBLIC_API_BASE_URL", "PUBLIC_WEBHOOK_BASE_URL", "PUBLIC_BASE_URL"],
        "CORS_ALLOWED_ORIGINS": ["CORS_ALLOWED_ORIGINS", "TECH_RESTORE_CORS_ORIGINS", "FRONTEND_ORIGIN"],
        "SMTP_HOST": ["SMTP_HOST"],
        "SMTP_PORT": ["SMTP_PORT"],
        "SMTP_USERNAME": ["SMTP_USERNAME"],
        "SMTP_PASSWORD": ["SMTP_PASSWORD"],
        "SMTP_FROM_EMAIL": ["SMTP_FROM_EMAIL"],
    }
    optional_voice_mail = {
        "TWILIO_ACCOUNT_SID": ["TWILIO_ACCOUNT_SID"],
        "TWILIO_AUTH_TOKEN": ["TWILIO_AUTH_TOKEN"],
        "TWILIO_PHONE_NUMBER": ["TWILIO_PHONE_NUMBER"],
    }

    missing_required = [label for label, names in required_any.items() if not any(_is_set(name) for name in names)]
    missing_optional = [label for label, names in optional_voice_mail.items() if not any(_is_set(name) for name in names)]

    auth_enabled_value = os.getenv("REPAIR_DESK_AUTH_ENABLED")
    if auth_enabled_value is None:
        missing_required.append("REPAIR_DESK_AUTH_ENABLED")

    if missing_required:
        missing_required_sorted = sorted(set(missing_required))
        logger.warning(
            "Production environment variables missing: %s",
            ", ".join(missing_required_sorted),
            extra={
                "action": "startup_env_validation",
                "missing_required": missing_required_sorted,
            },
        )

    if missing_optional:
        missing_optional_sorted = sorted(set(missing_optional))
        logger.warning(
            "Optional Twilio voicemail environment variables missing: %s",
            ", ".join(missing_optional_sorted),
            extra={
                "action": "startup_env_validation",
                "missing_optional": missing_optional_sorted,
            },
        )


def initialize_app() -> None:
    """Initialize application state before serving requests."""
    settings = get_settings()
    if settings.app_env.lower() in {"production", "staging"}:
        _log_production_env_warnings()
    initialize_monitoring(settings)
    initialize_database()
    try:
        AuthService.ensure_bootstrap_admin_invite_from_env()
    except ValueError as error:
        logger.warning("Bootstrap admin invite was not sent: %s", error)
    register_job_handlers()
    register_event_subscribers()
