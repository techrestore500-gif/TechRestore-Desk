from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from app.database import APP_ROOT, PERSISTENT_DATA_ROOT


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _to_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def _first_non_empty(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is None:
            continue
        trimmed = value.strip()
        if trimmed:
            return trimmed
    return None


def _merge_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)
    return merged


def _origin_from_url(raw_url: str | None) -> str | None:
    if raw_url is None:
        return None
    value = raw_url.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _infer_frontend_origin_from_public_api_base_url(public_api_base_url: str | None) -> str | None:
    origin = _origin_from_url(public_api_base_url)
    if origin is None:
        return None

    parsed = urlparse(origin)
    host = parsed.hostname or ""
    if not host.startswith("api."):
        return None

    desk_host = f"desk.{host.removeprefix('api.')}"
    if parsed.port:
        return f"{parsed.scheme}://{desk_host}:{parsed.port}"
    return f"{parsed.scheme}://{desk_host}"


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    log_json: bool
    cors_origins: list[str]
    sentry_dsn: str | None
    sentry_traces_sample_rate: float

    attachments_provider: str
    attachments_local_root: Path
    attachments_bucket: str | None
    attachments_region: str | None
    attachments_endpoint_url: str | None
    attachments_access_key_id: str | None
    attachments_secret_access_key: str | None
    attachments_signed_url_ttl_seconds: int
    attachments_max_file_size_bytes: int
    attachments_allowed_mime_types: list[str]

    jwt_secret: str
    signed_url_secret: str


DEFAULT_ALLOWED_ATTACHMENT_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
]

DEVELOPMENT_DEFAULT_SECRET = "dev-insecure-secret-change-me"
MINIMUM_SECRET_LENGTH = 32
OBVIOUS_SECRET_PLACEHOLDERS = {
    "changeme",
    "change-me",
    "replace-me",
    "placeholder",
    "your-secret",
    "your_jwt_secret",
    "secret",
    "password",
    "test",
    "example",
    DEVELOPMENT_DEFAULT_SECRET,
}


def _is_obvious_secret_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in OBVIOUS_SECRET_PLACEHOLDERS:
        return True
    if "change" in normalized and "secret" in normalized:
        return True
    if "placeholder" in normalized:
        return True
    if normalized.startswith("dev-") and "secret" in normalized:
        return True
    return False


def _validate_production_secret(value: str, *, env_name: str) -> None:
    if value == DEVELOPMENT_DEFAULT_SECRET:
        raise ValueError(f"{env_name} must be set in production/staging")
    if len(value) < MINIMUM_SECRET_LENGTH:
        raise ValueError(f"{env_name} must be at least {MINIMUM_SECRET_LENGTH} characters in production/staging")
    if _is_obvious_secret_placeholder(value):
        raise ValueError(f"{env_name} must not use an obvious placeholder value in production/staging")


def _resolve_jwt_secret() -> str:
    # Explicit precedence: dedicated JWT secret first, then legacy alias.
    return _first_non_empty("TECH_RESTORE_JWT_SECRET", "SECRET_KEY") or DEVELOPMENT_DEFAULT_SECRET


def _resolve_signed_url_secret(jwt_secret: str) -> str:
    # Explicit precedence: dedicated signed-url secret, then JWT/legacy aliases.
    return _first_non_empty("TECH_RESTORE_SIGNED_URL_SECRET", "TECH_RESTORE_JWT_SECRET", "SECRET_KEY") or jwt_secret


def get_settings() -> Settings:
    app_env = _first_non_empty("TECH_RESTORE_APP_ENV", "APP_ENV") or (
        "production" if (os.getenv("RENDER") or "").strip().lower() == "true" else "development"
    )
    local_root = os.getenv("TECH_RESTORE_ATTACHMENTS_LOCAL_ROOT")
    default_local_root = PERSISTENT_DATA_ROOT / "attachments"

    cors_origins = _to_list(
        _first_non_empty("TECH_RESTORE_CORS_ORIGINS", "CORS_ALLOWED_ORIGINS"),
        [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:6173",
            "http://localhost:6173",
        ],
    )
    frontend_origin = _origin_from_url(_first_non_empty("FRONTEND_ORIGIN", "FRONTEND_BASE_URL"))
    inferred_frontend_origin = _infer_frontend_origin_from_public_api_base_url(
        _first_non_empty("PUBLIC_API_BASE_URL", "PUBLIC_WEBHOOK_BASE_URL", "PUBLIC_BASE_URL")
    )
    cors_origins = _merge_unique([*cors_origins, frontend_origin or "", inferred_frontend_origin or ""])

    jwt_secret = _resolve_jwt_secret()
    signed_url_secret = _resolve_signed_url_secret(jwt_secret)

    settings = Settings(
        app_env=app_env,
        log_level=os.getenv("TECH_RESTORE_LOG_LEVEL", "INFO").upper(),
        log_json=_to_bool(os.getenv("TECH_RESTORE_LOG_JSON"), default=True),
        cors_origins=cors_origins,
        sentry_dsn=os.getenv("TECH_RESTORE_SENTRY_DSN"),
        sentry_traces_sample_rate=_to_float(os.getenv("TECH_RESTORE_SENTRY_TRACES_SAMPLE_RATE"), 0.0),
        attachments_provider=os.getenv("TECH_RESTORE_ATTACHMENTS_PROVIDER", "local").strip().lower(),
        attachments_local_root=Path(local_root).resolve() if local_root else default_local_root,
        attachments_bucket=os.getenv("TECH_RESTORE_ATTACHMENTS_BUCKET"),
        attachments_region=os.getenv("TECH_RESTORE_ATTACHMENTS_REGION"),
        attachments_endpoint_url=os.getenv("TECH_RESTORE_ATTACHMENTS_ENDPOINT_URL"),
        attachments_access_key_id=os.getenv("TECH_RESTORE_ATTACHMENTS_ACCESS_KEY_ID"),
        attachments_secret_access_key=os.getenv("TECH_RESTORE_ATTACHMENTS_SECRET_ACCESS_KEY"),
        attachments_signed_url_ttl_seconds=max(
            60,
            _to_int(os.getenv("TECH_RESTORE_ATTACHMENTS_SIGNED_URL_TTL_SECONDS"), 900),
        ),
        attachments_max_file_size_bytes=max(
            1024,
            _to_int(os.getenv("TECH_RESTORE_ATTACHMENTS_MAX_FILE_SIZE_BYTES"), 10 * 1024 * 1024),
        ),
        attachments_allowed_mime_types=_to_list(
            os.getenv("TECH_RESTORE_ATTACHMENTS_ALLOWED_MIME_TYPES"),
            DEFAULT_ALLOWED_ATTACHMENT_MIME_TYPES,
        ),
        jwt_secret=jwt_secret,
        signed_url_secret=signed_url_secret,
    )

    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if settings.attachments_provider not in {"local", "s3"}:
        raise ValueError("TECH_RESTORE_ATTACHMENTS_PROVIDER must be one of: local, s3")

    if settings.attachments_provider == "s3":
        missing = [
            key
            for key, value in {
                "TECH_RESTORE_ATTACHMENTS_BUCKET": settings.attachments_bucket,
                "TECH_RESTORE_ATTACHMENTS_REGION": settings.attachments_region,
                "TECH_RESTORE_ATTACHMENTS_ACCESS_KEY_ID": settings.attachments_access_key_id,
                "TECH_RESTORE_ATTACHMENTS_SECRET_ACCESS_KEY": settings.attachments_secret_access_key,
            }.items()
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing required S3 attachment settings: {joined}")

    if settings.app_env.lower() in {"production", "staging"}:
        _validate_production_secret(settings.jwt_secret, env_name="TECH_RESTORE_JWT_SECRET")
        _validate_production_secret(settings.signed_url_secret, env_name="TECH_RESTORE_SIGNED_URL_SECRET")
        if settings.attachments_provider == "local":
            attachments_root = settings.attachments_local_root.resolve()
            persistent_root = PERSISTENT_DATA_ROOT.resolve()
            persistent_prefix = persistent_root.as_posix().lower().rstrip("/") + "/"
            attachments_path = attachments_root.as_posix().lower()
            if not attachments_path.startswith(persistent_prefix):
                raise ValueError(
                    "TECH_RESTORE_ATTACHMENTS_LOCAL_ROOT must be under TECH_RESTORE_DATA_ROOT in production/staging"
                )

    if not settings.attachments_allowed_mime_types:
        raise ValueError("TECH_RESTORE_ATTACHMENTS_ALLOWED_MIME_TYPES cannot be empty")
