from fastapi.testclient import TestClient
import pytest
import re

import app.database as database
from app.main import app
from app.services.auth import AuthService
from app.services.emailer import EmailService


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
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_NAME", raising=False)
    monkeypatch.delenv("ADMIN_INVITE_ROLE", raising=False)
    monkeypatch.delenv("ADMIN_INVITE_BOOTSTRAP", raising=False)
    monkeypatch.delenv("ADMIN_INVITE_BOOTSTRAP_KEY", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_FROM_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_FROM_NAME", raising=False)
    monkeypatch.delenv("SMTP_USE_SSL", raising=False)
    monkeypatch.delenv("SMTP_STARTTLS", raising=False)
    monkeypatch.delenv("SMTP_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("FRONTEND_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_API_BASE_URL", raising=False)
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

    @staticmethod
    def _token_from_link(link: str) -> str:
        match = re.search(r"/invite/([^/?#]+)$", link)
        assert match is not None
        return match.group(1)

    @staticmethod
    def _capture_invite_emails(monkeypatch) -> list[dict]:
        sent: list[dict] = []

        def fake_send_invite_email(*, recipient_email: str, recipient_name: str | None, invite_link: str, expires_in_hours: int) -> None:
            sent.append(
                {
                    "recipient_email": recipient_email,
                    "recipient_name": recipient_name,
                    "invite_link": invite_link,
                    "expires_in_hours": expires_in_hours,
                }
            )

        monkeypatch.setattr(EmailService, "send_invite_email", staticmethod(fake_send_invite_email))
        return sent

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

    def test_me_succeeds_with_login_access_token(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")

        login_response = client.post("/api/auth/login", json={"email": "owner@example.com", "password": "pass12345"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        payload = me_response.json()
        assert payload["email"] == "owner@example.com"
        assert payload["role"] == "owner"

    def test_change_password_success_and_old_password_stops_working(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")

        login_response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "pass12345"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        change_password_response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "pass12345",
                "new_password": "new-pass-456",
                "confirm_password": "new-pass-456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert change_password_response.status_code == 200

        old_password_login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "pass12345"})
        assert old_password_login.status_code == 401

        new_password_login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "new-pass-456"})
        assert new_password_login.status_code == 200

    def test_change_password_fails_with_wrong_current_password(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        token = self._login(client, "admin@example.com")["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "wrong-pass-123",
                "new_password": "new-pass-456",
                "confirm_password": "new-pass-456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "current password is incorrect" in response.json()["detail"].lower()

    def test_change_password_rejects_mismatched_confirmation(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        token = self._login(client, "admin@example.com")["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "pass12345",
                "new_password": "new-pass-456",
                "confirm_password": "different-pass-456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "do not match" in response.json()["detail"].lower()

    def test_login_invalid_credentials(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

        response = client.post("/api/auth/login", json={"email": "missing@example.com", "password": "nope12345"})
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_admin_can_create_pending_invite(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        monkeypatch.setenv("FRONTEND_BASE_URL", "https://desk.example.com")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        sent = self._capture_invite_emails(monkeypatch)
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
        assert len(sent) == 1
        assert sent[0]["recipient_email"] == "pending@example.com"
        assert sent[0]["invite_link"].startswith("https://desk.example.com/invite/")

    def test_non_admin_cannot_create_invites(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._capture_invite_emails(monkeypatch)
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
        sent = self._capture_invite_emails(monkeypatch)
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = self._login(client, "admin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Tech User", "email": "techuser@example.com", "role": "technician"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

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
        sent = self._capture_invite_emails(monkeypatch)
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Single Use", "email": "single@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

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
        sent = self._capture_invite_emails(monkeypatch)
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Revoked User", "email": "revoked@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        invite = invite_response.json()
        token = self._token_from_link(sent[-1]["invite_link"])

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
        sent = self._capture_invite_emails(monkeypatch)
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = self._login(client, "admin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Expired User", "email": "expired@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

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

    def test_bootstrap_invite_is_emailed_once_without_spam(self, client, monkeypatch):
        sent = self._capture_invite_emails(monkeypatch)
        monkeypatch.setenv("ADMIN_EMAIL", "mattiskleinbh@gmail.com")
        monkeypatch.setenv("ADMIN_NAME", "Mattis Klein")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP", "true")
        monkeypatch.setenv("ADMIN_INVITE_ROLE", "owner")

        first = AuthService.ensure_bootstrap_admin_invite_from_env()
        assert first is not None
        assert first["email"] == "mattiskleinbh@gmail.com"
        assert first["role"] == "owner"
        assert len(sent) == 1

        second = AuthService.ensure_bootstrap_admin_invite_from_env()
        assert second is not None
        assert second["status"] == "pending"
        assert len(sent) == 1

    def test_bootstrap_invite_can_be_created_without_email(self, client, monkeypatch):
        sent = self._capture_invite_emails(monkeypatch)
        monkeypatch.setenv("ADMIN_EMAIL", "mattiskleinbh@gmail.com")
        monkeypatch.setenv("ADMIN_NAME", "Mattis Klein")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP", "true")
        monkeypatch.setenv("ADMIN_INVITE_ROLE", "owner")

        invite = AuthService.ensure_bootstrap_admin_invite_from_env(send_email=False)
        assert invite is not None
        assert invite["email"] == "mattiskleinbh@gmail.com"
        assert invite["status"] == "pending"
        assert len(sent) == 0

    def test_bootstrap_resend_requires_valid_bootstrap_key(self, client, monkeypatch):
        self._capture_invite_emails(monkeypatch)
        monkeypatch.setenv("ADMIN_EMAIL", "mattiskleinbh@gmail.com")
        monkeypatch.setenv("ADMIN_NAME", "Mattis Klein")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP", "true")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP_KEY", "bootstrap-secret")

        forbidden = client.post("/api/auth/bootstrap/resend")
        assert forbidden.status_code == 403

        allowed = client.post("/api/auth/bootstrap/resend", headers={"X-Bootstrap-Key": "bootstrap-secret"})
        assert allowed.status_code == 200
        assert allowed.json()["status"] == "pending"
        assert allowed.json()["email"] == "mattiskleinbh@gmail.com"

    def test_bootstrap_resend_reissues_invite_without_db_reset(self, client, monkeypatch):
        sent = self._capture_invite_emails(monkeypatch)
        monkeypatch.setenv("ADMIN_EMAIL", "mattiskleinbh@gmail.com")
        monkeypatch.setenv("ADMIN_NAME", "Mattis Klein")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP", "true")
        monkeypatch.setenv("ADMIN_INVITE_ROLE", "owner")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP_KEY", "bootstrap-secret")

        first = client.post("/api/auth/bootstrap/resend", headers={"X-Bootstrap-Key": "bootstrap-secret"})
        assert first.status_code == 200
        first_invite_id = first.json()["id"]

        second = client.post("/api/auth/bootstrap/resend", headers={"X-Bootstrap-Key": "bootstrap-secret"})
        assert second.status_code == 200
        second_invite_id = second.json()["id"]
        assert second_invite_id != first_invite_id
        assert len(sent) == 2

        with database.get_connection() as connection:
            previous = connection.execute(
                "SELECT status FROM auth_invites WHERE id = ?",
                (first_invite_id,),
            ).fetchone()
            assert previous is not None
            assert previous["status"] == "revoked"

    def test_bootstrap_resend_blocked_after_admin_exists(self, client, monkeypatch):
        self._capture_invite_emails(monkeypatch)
        monkeypatch.setenv("ADMIN_EMAIL", "mattiskleinbh@gmail.com")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP", "true")
        monkeypatch.setenv("ADMIN_INVITE_BOOTSTRAP_KEY", "bootstrap-secret")

        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")

        response = client.post("/api/auth/bootstrap/resend", headers={"X-Bootstrap-Key": "bootstrap-secret"})
        assert response.status_code == 400
        assert "unavailable" in response.json()["detail"].lower()

    def test_admin_can_resend_pending_or_expired_invite(self, client, monkeypatch):
        sent = self._capture_invite_emails(monkeypatch)
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]

        create_response = client.post(
            "/api/auth/invites",
            json={"name": "Resend User", "email": "resend@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert create_response.status_code == 201
        original_id = create_response.json()["id"]
        assert len(sent) == 1

        resend_pending = client.post(
            f"/api/auth/invites/{original_id}/resend",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert resend_pending.status_code == 200
        assert resend_pending.json()["status"] == "pending"
        assert len(sent) == 2

        with database.get_connection() as connection:
            connection.execute(
                "UPDATE auth_invites SET expires_at = datetime('now', '-1 day') WHERE id = ?",
                (resend_pending.json()["id"],),
            )
            connection.commit()

        resend_expired = client.post(
            f"/api/auth/invites/{resend_pending.json()['id']}/resend",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert resend_expired.status_code == 200
        assert resend_expired.json()["status"] == "pending"
        assert len(sent) == 3

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

    # -------------------------------------------------------------------------
    # Production bug regression: invite-accept / login with shared password set
    # -------------------------------------------------------------------------

    def test_invite_accepted_owner_can_login_when_shared_password_also_set(self, client, monkeypatch):
        """
        Production regression test.
        When REPAIR_DESK_AUTH_ENABLED=true and REPAIR_DESK_PASSWORD is set,
        an invite-accepted user must be able to log in with their own password.
        The shared-password must not intercept per-user auth.
        """
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "shared-prod-pass")
        sent = self._capture_invite_emails(monkeypatch)

        # Bootstrap owner accepts invite
        self._create_user(name="Bootstrap Admin", email="bootstrapadmin@example.com", username="bootstrapadmin1", role="owner")
        admin_token = self._login(client, "bootstrapadmin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Owner User", "email": "owner@example.com", "role": "owner"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

        accept_response = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "owner-invite-pass-456"},
        )
        assert accept_response.status_code == 200
        accepted_user = accept_response.json()["user"]
        assert accepted_user["status"] == "active"
        assert accepted_user["role"] == "owner"

        # Per-user password must succeed even though shared password is set
        login_response = client.post(
            "/api/auth/login",
            json={"email": "owner@example.com", "password": "owner-invite-pass-456"},
        )
        assert login_response.status_code == 200
        payload = login_response.json()
        assert payload["user"]["email"] == "owner@example.com"
        assert payload["user"]["role"] == "owner"
        assert payload["user"]["id"] != 0  # must be the real DB user, not shared-password ghost

    def test_invite_accepted_user_wrong_password_returns_401_when_shared_password_set(self, client, monkeypatch):
        """Per-user wrong password must still return 401 even when shared-password mode is active."""
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "shared-prod-pass")
        sent = self._capture_invite_emails(monkeypatch)

        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = self._login(client, "admin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Tech", "email": "tech@example.com", "role": "technician"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

        client.post(f"/api/auth/invites/{token}/accept", json={"password": "correct-pass-999"})

        wrong = client.post("/api/auth/login", json={"email": "tech@example.com", "password": "wrong-pass"})
        assert wrong.status_code == 401
        assert "Invalid credentials" in wrong.json()["detail"]

    def test_shared_password_fallback_still_works_when_no_per_user_account(self, client, monkeypatch):
        """Shared-password fallback must still authenticate when no individual user exists for the email."""
        monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "true")
        monkeypatch.setenv("REPAIR_DESK_PASSWORD", "shared-prod-pass")

        response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "shared-prod-pass"})
        assert response.status_code == 200
        assert response.json()["user"]["id"] == 0

    def test_invite_accept_creates_active_owner_user(self, client, monkeypatch):
        """Accepting an owner invite must produce a user with status=active, is_active=True, role=owner."""
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        sent = self._capture_invite_emails(monkeypatch)
        self._create_user(name="Owner", email="owner@example.com", username="owner1", role="owner")
        owner_token = self._login(client, "owner@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "New Owner", "email": "newowner@example.com", "role": "owner"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

        accept_response = client.post(
            f"/api/auth/invites/{token}/accept",
            json={"password": "owner-pass-321"},
        )
        assert accept_response.status_code == 200
        user = accept_response.json()["user"]
        assert user["status"] == "active"
        assert user["is_active"] is True
        assert user["role"] == "owner"
        assert user["email"] == "newowner@example.com"

    def test_accepted_invite_is_single_use_even_after_login(self, client, monkeypatch):
        """An already-accepted invite token must be rejected on a second accept attempt."""
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        sent = self._capture_invite_emails(monkeypatch)
        self._create_user(name="Admin", email="admin@example.com", username="admin1", role="admin")
        admin_token = self._login(client, "admin@example.com")["access_token"]

        invite_response = client.post(
            "/api/auth/invites",
            json={"name": "Single Use", "email": "singleuse@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert invite_response.status_code == 201
        token = self._token_from_link(sent[-1]["invite_link"])

        first = client.post(f"/api/auth/invites/{token}/accept", json={"password": "single-pass-123"})
        assert first.status_code == 200

        # Login after first accept must succeed
        login = client.post("/api/auth/login", json={"email": "singleuse@example.com", "password": "single-pass-123"})
        assert login.status_code == 200

        # Second accept of same token must fail
        second = client.post(f"/api/auth/invites/{token}/accept", json={"password": "single-pass-123"})
        assert second.status_code == 400
        assert "not available" in second.json()["detail"].lower()

    def test_login_email_is_case_insensitive(self, client, monkeypatch):
        """Login must succeed regardless of email case because lookup uses LOWER(email)."""
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        self._create_user(name="Case User", email="CaseUser@Example.COM", username="caseuser1", role="viewer")

        lower = client.post("/api/auth/login", json={"email": "caseuser@example.com", "password": "pass12345"})
        assert lower.status_code == 200

        upper = client.post("/api/auth/login", json={"email": "CASEUSER@EXAMPLE.COM", "password": "pass12345"})
        assert upper.status_code == 200
