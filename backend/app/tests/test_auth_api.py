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

    @staticmethod
    def _login(client: TestClient, email: str, password: str = "pass12345") -> dict:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200
        return response.json()

    def test_shared_password_login_without_existing_user(self, client, monkeypatch):
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "unit-test-shared-password")

        response = client.post("/api/auth/login", json={"email": "desk@example.com", "password": "unit-test-shared-password"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["role"] == "admin"
        assert payload["user"]["id"] == 0

    def test_shared_password_login_rejects_invalid_password(self, client, monkeypatch):
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "unit-test-shared-password")

        response = client.post("/api/auth/login", json={"email": "desk@example.com", "password": "wrongpass"})
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

        login_resp = client.post("/api/auth/login", json={"email": "desk@example.com", "password": "unit-test-shared-password"})
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

    def test_login_success_with_email(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin One", email="admin1@example.com", username="admin1", role="admin")

        response = client.post("/api/auth/login", json={"email": "admin1@example.com", "password": "pass12345"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["user"]["email"] == "admin1@example.com"

    def test_login_invalid_credentials(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.post("/api/auth/login", json={"email": "missing@example.com", "password": "nope12345"})
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_admin_can_create_pending_invite(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        admin_token = self._login(client, "owner@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Pending User", "email": "pending@example.com", "role": "technician"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert invite_response.status_code == 201
        payload = invite_response.json()
        assert payload["email"] == "pending@example.com"
        assert payload["role"] == "technician"
        assert payload["status"] == "pending"
        assert payload["invite_link"].endswith("/invite/" + payload["invite_link"].split("/invite/")[-1])

    def test_non_admin_cannot_create_invites(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Front Desk", email="desk@example.com", username="desk1", role="front_desk")
        front_desk_token = self._login(client, "desk@example.com")["access_token"]

        response = client.post(
            "/api/auth/invites",
            json={"name": "New User", "email": "newuser@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {front_desk_token}"},
        )
        assert response.status_code == 403

    def test_invite_acceptance_activates_user_and_allows_login(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = self._login(client, "admin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Tech User", "email": "techuser@example.com", "role": "technician"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        token = invite_response.json()["invite_link"].split("/invite/")[-1]

        resolve_response = client.get(f"/api/auth/invites/{token}")
        assert resolve_response.status_code == 200
        assert resolve_response.json()["email"] == "techuser@example.com"

        accept_response = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "tech-pass-123"},
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["user"]["status"] == "active"
        assert accept_response.json()["user"]["role"] == "technician"

        login = client.post(
            "/api/auth/login",
            json={"email": "techuser@example.com", "password": "tech-pass-123"},
        )
        assert login.status_code == 200

    def test_invite_token_is_single_use(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Single Use", "email": "single@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        token = invite_response.json()["invite_link"].split("/invite/")[-1]

        first_accept = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "single-pass-123"},
        )
        assert first_accept.status_code == 200

        second_accept = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "single-pass-123"},
        )
        assert second_accept.status_code == 400

    def test_revoked_invite_cannot_be_accepted(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Revoked User", "email": "revoked@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        invite = invite_response.json()
        token = invite["invite_link"].split("/invite/")[-1]

        revoke_response = client.post(
            f"/api/auth/invites/{invite['id']}/revoke",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert revoke_response.status_code == 200
        assert revoke_response.json()["status"] == "revoked"

        accept_response = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "revoked-pass-123"},
        )
        assert accept_response.status_code == 400
        assert "not available" in accept_response.json()["detail"].lower()

    def test_expired_invite_cannot_be_resolved_or_accepted(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = self._login(client, "admin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Expired User", "email": "expired@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        token = invite_response.json()["invite_link"].split("/invite/")[-1]

        invite_id = invite_response.json()["id"]
        with database.get_connection() as connection:
            connection.execute(
                "UPDATE auth_invites SET expires_at = datetime('now', '-1 day') WHERE id = ?",
                (invite_id,),
            )
            connection.commit()

        resolve_response = client.get(f"/api/auth/invites/{token}")
        assert resolve_response.status_code == 400
        assert "not available" in resolve_response.json()["detail"].lower()

        accept_response = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "expired-pass-123"},
        )
        assert accept_response.status_code == 400
        assert "expired" in accept_response.json()["detail"].lower()

    def test_bootstrap_invite_link_endpoint_requires_key(self, client, monkeypatch):
        monkeypatch.setenv("ADMIN_EMAIL", "techrestore500@gmail.com")
        monkeypatch.setenv("ADMIN_NAME", "Tech Restore Owner")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP_KEY", "bootstrap-secret")

        without_key = client.post("/api/auth/bootstrap/invite-link")
        assert without_key.status_code == 403

        with_key = client.post("/api/auth/bootstrap/invite-link", headers={"X-Bootstrap-Key": "bootstrap-secret"})
        assert with_key.status_code == 200
        payload = with_key.json()
        assert payload["email"] == "techrestore500@gmail.com"
        assert "/invite/" in payload["invite_link"]

    def test_disabled_user_cannot_login(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]
        self._create_user(name="Viewer", email="viewer@example.com", username="viewer1", role="viewer")

        users = client.get("/api/auth/users", headers={"Authorization": f"Bearer {owner_token}"}).json()
        viewer = next(item for item in users if item["email"] == "viewer@example.com")

        with database.get_connection() as connection:
            connection.execute("UPDATE users SET status = 'disabled', is_active = 0 WHERE id = ?", (viewer["id"],))
            connection.commit()

        login = client.post("/api/auth/login", json={"email": "viewer@example.com", "password": "pass12345"})
        assert login.status_code == 401
        assert "disabled" in login.json()["detail"].lower()

    def test_protected_route_requires_token(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.patch("/api/pricing/rules", json={"diagnostic_fee": 20})
        assert response.status_code == 401

    def test_role_forbidden_on_admin_route(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Tech One", email="tech1@example.com", username="tech1", role="technician")

        login_resp = client.post("/api/auth/login", json={"email": "tech1@example.com", "password": "pass12345"})
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

        login_resp = client.post("/api/auth/login", json={"email": "admin2@example.com", "password": "pass12345"})
        token = login_resp.json()["access_token"]

        response = client.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 22},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["defaults"]["diagnostic_fee"] == 22
