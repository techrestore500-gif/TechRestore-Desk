import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.core.settings import get_settings, validate_settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)
    monkeypatch.delenv("REPAIR_DESK_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("REPAIR_DESK_PASSWORD", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("TECH_RESTORE_APP_ENV", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_PHONE_NUMBER", raising=False)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_NAME", raising=False)
    monkeypatch.delenv("ADMIN_INVITE_ROLE", raising=False)
    monkeypatch.delenv("ADMIN_INVITE_BOOTSTRAP", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_FROM_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_FROM_NAME", raising=False)
    monkeypatch.delenv("FRONTEND_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_WEBHOOK_BASE_URL", raising=False)

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


def test_validation_error_includes_standardized_error_envelope(client: TestClient):
    response = client.post(
        "/api/customers",
        json={"full_name": "No Phone"},
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["detail"] == "Request validation failed"
    assert payload.get("request_id")


def test_settings_validation_requires_non_default_secrets_in_production(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", "dev-insecure-secret-change-me")
    monkeypatch.delenv("TECH_RESTORE_SIGNED_URL_SECRET", raising=False)

    with pytest.raises(ValueError):
        get_settings()


def test_settings_validation_requires_s3_fields(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_PROVIDER", "s3")
    monkeypatch.delenv("TECH_RESTORE_ATTACHMENTS_BUCKET", raising=False)
    monkeypatch.delenv("TECH_RESTORE_ATTACHMENTS_REGION", raising=False)
    monkeypatch.delenv("TECH_RESTORE_ATTACHMENTS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("TECH_RESTORE_ATTACHMENTS_SECRET_ACCESS_KEY", raising=False)

    with pytest.raises(ValueError):
        get_settings()

    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_BUCKET", "tech-restore-private")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_REGION", "auto")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_SECRET_ACCESS_KEY", "y")
    settings = get_settings()
    validate_settings(settings)
    assert settings.attachments_provider == "s3"


def test_frontend_origin_is_included_in_cors_origins(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://desk.example.com")
    settings = get_settings()
    assert "https://desk.example.com" in settings.cors_origins


def test_cors_allowed_origins_alias_is_supported(monkeypatch):
    monkeypatch.delenv("TECH_RESTORE_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://desk.example.com,https://desk2.example.com")
    settings = get_settings()
    assert "https://desk.example.com" in settings.cors_origins
    assert "https://desk2.example.com" in settings.cors_origins


def test_secret_key_alias_is_supported(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.delenv("TECH_RESTORE_JWT_SECRET", raising=False)
    monkeypatch.delenv("TECH_RESTORE_SIGNED_URL_SECRET", raising=False)
    monkeypatch.setenv("SECRET_KEY", "prod-secret-key")

    settings = get_settings()
    assert settings.jwt_secret == "prod-secret-key"
    assert settings.signed_url_secret == "prod-secret-key"
