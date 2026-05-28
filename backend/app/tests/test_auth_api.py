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
    monkeypatch.delenv("REPAIR_DESK_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("REPAIR_DESK_PASSWORD", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("TECH_RESTORE_APP_ENV", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_PHONE_NUMBER", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_WEBHOOK_BASE_URL", raising=False)

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


class TestAuthApi:
    @staticmethod
    def _create_user(*, name: str, email: str, username: str, role: str, password: str = "pass12345") -> dict:
        return AuthService.create_user(name=name, email=email, username=username, password=password, role=role)

    def test_shared_password_login_without_existing_user(self, client, monkeypatch):
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "unit-test-shared-password")

        response = client.post("/api/auth/login", json={"identifier": "desk", "password": "unit-test-shared-password"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["role"] == "admin"
        assert payload["user"]["id"] == 0

    def test_shared_password_login_rejects_invalid_password(self, client, monkeypatch):
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "unit-test-shared-password")

        response = client.post("/api/auth/login", json={"identifier": "desk", "password": "wrongpass"})
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_shared_password_mode_protects_private_routes_but_allows_twilio_webhooks(self, client, monkeypatch):
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "unit-test-shared-password")

        private_response = client.get("/api/settings/twilio")
        assert private_response.status_code == 401

        webhook_response = client.post("/api/twilio/voice", data={"From": "+1", "To": "+2"})
        assert webhook_response.status_code == 200

    def test_shared_password_token_can_access_private_admin_routes(self, client, monkeypatch):
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "unit-test-shared-password")

        login_resp = client.post("/api/auth/login", json={"identifier": "desk", "password": "unit-test-shared-password"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        twilio_settings_resp = client.get(
            "/api/settings/twilio",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert twilio_settings_resp.status_code == 200

        pricing_rules_resp = client.get(
            "/api/pricing/rules",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert pricing_rules_resp.status_code == 200

    def test_login_success_with_username_or_email(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin One", email="admin1@example.com", username="admin1", role="admin")

        response = client.post("/api/auth/login", json={"identifier": "admin1", "password": "pass12345"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["username"] == "admin1"

        email_response = client.post("/api/auth/login", json={"identifier": "admin1@example.com", "password": "pass12345"})
        assert email_response.status_code == 200
        assert email_response.json()["user"]["email"] == "admin1@example.com"

    def test_login_invalid_credentials(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.post("/api/auth/login", json={"identifier": "missing", "password": "nope1234"})
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_signup_creates_pending_request_and_prevents_login(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        signup = client.post(
            "/api/auth/signup",
            json={"name": "Pending User", "email": "pending@example.com", "password": "pending-pass-123"},
        )
        assert signup.status_code == 201
        assert "submitted" in signup.json()["message"].lower()

        login = client.post(
            "/api/auth/login",
            json={"identifier": "pending@example.com", "password": "pending-pass-123"},
        )
        assert login.status_code == 401
        assert "pending approval" in login.json()["detail"].lower()

    def test_signup_rejects_duplicate_pending_or_active_email(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        first = client.post(
            "/api/auth/signup",
            json={"name": "Pending User", "email": "dupe@example.com", "password": "pending-pass-123"},
        )
        assert first.status_code == 201

        duplicate_pending = client.post(
            "/api/auth/signup",
            json={"name": "Pending User 2", "email": "dupe@example.com", "password": "pending-pass-123"},
        )
        assert duplicate_pending.status_code == 400

        self._create_user(name="Active User", email="active@example.com", username="active1", role="admin")
        duplicate_active = client.post(
            "/api/auth/signup",
            json={"name": "Active User 2", "email": "active@example.com", "password": "pending-pass-123"},
        )
        assert duplicate_active.status_code == 400

    def test_admin_can_approve_pending_and_assign_role(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")

        login_admin = client.post("/api/auth/login", json={"identifier": "owner1", "password": "pass12345"})
        admin_token = login_admin.json()["access_token"]

        signup = client.post(
            "/api/auth/signup",
            json={"name": "Request User", "email": "request@example.com", "password": "request-pass-123"},
        )
        assert signup.status_code == 201

        pending = client.get("/api/auth/access-requests", headers={"Authorization": f"Bearer {admin_token}"})
        assert pending.status_code == 200
        request_user = next(item for item in pending.json() if item["email"] == "request@example.com")

        approve = client.post(
            f"/api/auth/access-requests/{request_user['id']}/approve",
            json={"role": "technician"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert approve.status_code == 200
        assert approve.json()["user"]["status"] == "active"
        assert approve.json()["user"]["role"] == "technician"

        login_approved = client.post(
            "/api/auth/login",
            json={"identifier": "request@example.com", "password": "request-pass-123"},
        )
        assert login_approved.status_code == 200

    def test_admin_can_deny_pending_and_login_stays_blocked(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = client.post("/api/auth/login", json={"identifier": "admin1", "password": "pass12345"}).json()["access_token"]

        signup = client.post(
            "/api/auth/signup",
            json={"name": "Denied User", "email": "denied@example.com", "password": "denied-pass-123"},
        )
        assert signup.status_code == 201

        pending = client.get("/api/auth/access-requests", headers={"Authorization": f"Bearer {admin_token}"})
        request_user = next(item for item in pending.json() if item["email"] == "denied@example.com")

        deny = client.post(
            f"/api/auth/access-requests/{request_user['id']}/deny",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert deny.status_code == 200
        assert deny.json()["user"]["status"] == "denied"

        login = client.post(
            "/api/auth/login",
            json={"identifier": "denied@example.com", "password": "denied-pass-123"},
        )
        assert login.status_code == 401
        assert "denied" in login.json()["detail"].lower()

    def test_disabled_user_cannot_login(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = client.post("/api/auth/login", json={"identifier": "owner1", "password": "pass12345"}).json()["access_token"]
        self._create_user(name="Viewer", email="viewer@example.com", username="viewer1", role="viewer")

        users = client.get("/api/auth/users", headers={"Authorization": f"Bearer {owner_token}"}).json()
        viewer = next(item for item in users if item["email"] == "viewer@example.com")

        with database.get_connection() as connection:
            connection.execute("UPDATE users SET status = 'disabled', is_active = 0 WHERE id = ?", (viewer["id"],))
            connection.commit()

        login = client.post("/api/auth/login", json={"identifier": "viewer1", "password": "pass12345"})
        assert login.status_code == 401
        assert "disabled" in login.json()["detail"].lower()

    def test_non_admin_cannot_approve_requests(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Front Desk", email="desk@example.com", username="desk1", role="front_desk")
        front_desk_token = client.post("/api/auth/login", json={"identifier": "desk1", "password": "pass12345"}).json()["access_token"]

        client.post(
            "/api/auth/signup",
            json={"name": "Request User", "email": "request2@example.com", "password": "request-pass-123"},
        )

        list_resp = client.get("/api/auth/access-requests", headers={"Authorization": f"Bearer {front_desk_token}"})
        assert list_resp.status_code == 403

    def test_protected_route_requires_token(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.patch("/api/pricing/rules", json={"diagnostic_fee": 20})
        assert response.status_code == 401

    def test_role_forbidden_on_admin_route(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Tech One", email="tech1@example.com", username="tech1", role="technician")

        login_resp = client.post("/api/auth/login", json={"identifier": "tech1", "password": "pass12345"})
        token = login_resp.json()["access_token"]

        response = client.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_role_allowed_on_admin_route(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin Two", email="admin2@example.com", username="admin2", role="admin")

        login_resp = client.post("/api/auth/login", json={"identifier": "admin2", "password": "pass12345"})
        token = login_resp.json()["access_token"]

        response = client.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 22},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["defaults"]["diagnostic_fee"] == 22
