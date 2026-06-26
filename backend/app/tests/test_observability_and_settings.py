from pathlib import Path

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


def test_frontend_base_url_is_included_in_cors_origins(monkeypatch):
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://desk.example.com/some/path")
    settings = get_settings()
    assert "https://desk.example.com" in settings.cors_origins


def test_public_api_base_url_infers_desk_origin_for_cors(monkeypatch):
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    monkeypatch.delenv("FRONTEND_BASE_URL", raising=False)
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
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


def test_runtime_diagnostics_flags_non_persistent_sqlite_path(client: TestClient, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", database.DEFAULT_DB_PATH)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/tech_restore_desk.sqlite")

    response = client.get("/api/system/runtime-diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["database_type"] == "sqlite"
    assert payload["database_url_configured"] is True
    assert payload["sqlite_under_var_data"] is False
    assert payload["persistence_status"] == "ephemeral_or_unknown"
    assert "persistent storage" in payload["warning"]
    assert payload["database_path"].startswith("local:/")


def test_runtime_diagnostics_flags_var_data_sqlite_path_as_persistent(client: TestClient, monkeypatch):
    monkeypatch.setattr(database, "PERSISTENT_DATA_ROOT", Path("/var/data"))
    monkeypatch.setattr(database, "DB_PATH", Path("/var/data/tech_restore_desk.sqlite"))
    monkeypatch.setenv("DATABASE_URL", "sqlite:////var/data/tech_restore_desk.sqlite")

    response = client.get("/api/system/runtime-diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["database_type"] == "sqlite"
    assert payload["database_path"] == "persistent:/tech_restore_desk.sqlite"
    assert payload["sqlite_under_var_data"] is True
    assert payload["persistence_status"] == "persistent_disk"
    assert payload["warning"] is None


def test_runtime_diagnostics_reports_local_attachment_persistence(client: TestClient, monkeypatch):
    monkeypatch.setattr(database, "PERSISTENT_DATA_ROOT", Path("/var/data"))
    monkeypatch.setattr(database, "DB_PATH", Path("/var/data/tech_restore_desk.sqlite"))
    monkeypatch.setenv("DATABASE_URL", "sqlite:////var/data/tech_restore_desk.sqlite")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_PROVIDER", "local")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_LOCAL_ROOT", "/var/data/attachments")

    response = client.get("/api/system/runtime-diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["attachments_path"] == "persistent:/attachments"
    assert payload["attachments_persistent"] is True


def test_runtime_diagnostics_reports_s3_attachment_mode(client: TestClient, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", Path("/var/data/tech_restore_desk.sqlite"))
    monkeypatch.setenv("DATABASE_URL", "sqlite:////var/data/tech_restore_desk.sqlite")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_PROVIDER", "s3")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_BUCKET", "tech-restore-private")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_REGION", "auto")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_SECRET_ACCESS_KEY", "y")

    response = client.get("/api/system/runtime-diagnostics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["attachments_path"] == "s3"
    assert payload["attachments_persistent"] is None


def test_production_requires_existing_persistent_data_root(monkeypatch, tmp_path):
    missing_root = tmp_path / "missing-persistent-root"
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.setattr(database, "PERSISTENT_DATA_ROOT", missing_root)
    monkeypatch.setattr(database, "DB_PATH", missing_root / "tech_restore_desk.sqlite")
    monkeypatch.setattr(database, "BACKUPS_DIR", missing_root / "backups")

    with pytest.raises(RuntimeError):
        database.initialize_database()


def test_production_unwritable_persistent_root_fails_startup(monkeypatch, tmp_path):
    root = tmp_path / "persistent-root"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.setattr(database, "PERSISTENT_DATA_ROOT", root)
    monkeypatch.setattr(database, "DB_PATH", root / "tech_restore_desk.sqlite")
    monkeypatch.setattr(database, "BACKUPS_DIR", root / "backups")

    def _raise_unwritable(_path):
        raise PermissionError("not writable")

    monkeypatch.setattr(database, "_assert_directory_writable", _raise_unwritable)

    with pytest.raises(PermissionError):
        database.initialize_database()


def test_production_local_attachments_cannot_use_non_persistent_path(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", "prod-secret-key")
    monkeypatch.setenv("TECH_RESTORE_SIGNED_URL_SECRET", "prod-signed-secret")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_PROVIDER", "local")
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_LOCAL_ROOT", "C:/tmp/nonpersistent-attachments")

    with pytest.raises(ValueError):
        get_settings()
