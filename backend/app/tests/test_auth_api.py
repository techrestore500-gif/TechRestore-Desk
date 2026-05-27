from fastapi.testclient import TestClient
import pytest

import app.database as database
from app.main import app
from app.services.auth import AuthService


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_auth_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


class TestAuthApi:
    def test_login_success(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        AuthService.create_user(username="admin1", password="pass12345", role="admin")

        response = client.post("/api/auth/login", json={"username": "admin1", "password": "pass12345"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["username"] == "admin1"

    def test_login_invalid_credentials(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.post("/api/auth/login", json={"username": "missing", "password": "nope1234"})
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_protected_route_requires_token(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.patch("/api/pricing/rules", json={"diagnostic_fee": 20})
        assert response.status_code == 401

    def test_role_forbidden_on_admin_route(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        AuthService.create_user(username="tech1", password="pass12345", role="technician")

        login_resp = client.post("/api/auth/login", json={"username": "tech1", "password": "pass12345"})
        token = login_resp.json()["access_token"]

        response = client.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_role_allowed_on_admin_route(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        AuthService.create_user(username="admin2", password="pass12345", role="admin")

        login_resp = client.post("/api/auth/login", json={"username": "admin2", "password": "pass12345"})
        token = login_resp.json()["access_token"]

        response = client.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 22},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["defaults"]["diagnostic_fee"] == 22
