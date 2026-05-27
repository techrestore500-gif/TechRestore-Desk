import json

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app
from app.services.auth import AuthService


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_audit_test.sqlite"
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


def _latest_activity(action: str) -> dict | None:
    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM activity_logs WHERE action = ? ORDER BY id DESC LIMIT 1",
            (action,),
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    for key in ("old_value", "new_value"):
        if item.get(key):
            item[key] = json.loads(item[key])
    return item


def _count_activity(action: str) -> int:
    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM activity_logs WHERE action = ?",
            (action,),
        ).fetchone()
    return int(row["count"])


class TestAuditApi:
    def test_pricing_update_audit_has_request_and_user(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        admin = AuthService.create_user(username="auditadmin", password="pass12345", role="admin")

        login_resp = client.post(
            "/api/auth/login",
            json={"username": "auditadmin", "password": "pass12345"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        request_id = "req_audit_test_001"
        response = client.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 33},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Request-ID": request_id,
            },
        )
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == request_id

        activity = _latest_activity("pricing_rules_updated")
        assert activity is not None
        assert activity["user_id"] == admin["id"]
        assert activity["request_id"] == request_id
        assert activity["entity_type"] == "pricing_defaults"
        assert activity["old_value"]["diagnostic_fee"] != activity["new_value"]["diagnostic_fee"]

    def test_ticket_status_change_generates_audit(self, client):
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Audit Customer", "primary_phone": "555-1414"},
        )
        customer_id = customer_resp.json()["id"]

        ticket_resp = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Audit Flow"},
        )
        ticket_id = ticket_resp.json()["id"]

        status_resp = client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"new_status": "Needs Diagnosis", "changed_by": "AuditTech"},
        )
        assert status_resp.status_code == 201

        activity = _latest_activity("ticket_status_changed")
        assert activity is not None
        assert activity["entity_id"] == ticket_id
        assert activity["old_value"]["status"] == "New Intake"
        assert activity["new_value"]["status"] == "Needs Diagnosis"

    def test_failed_status_transition_does_not_create_audit(self, client):
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Failure Customer", "primary_phone": "555-1515"},
        )
        customer_id = customer_resp.json()["id"]

        ticket_resp = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Failure Flow"},
        )
        ticket_id = ticket_resp.json()["id"]

        before = _count_activity("ticket_status_changed")
        invalid_resp = client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"new_status": "Ready for Pickup", "changed_by": "AuditTech"},
        )
        assert invalid_resp.status_code == 422

        after = _count_activity("ticket_status_changed")
        assert after == before

    def test_admin_user_create_action_is_audited(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
        AuthService.create_user(username="superadmin", password="pass12345", role="admin")

        login_resp = client.post(
            "/api/auth/login",
            json={"username": "superadmin", "password": "pass12345"},
        )
        token = login_resp.json()["access_token"]

        create_resp = client.post(
            "/api/auth/users",
            json={"username": "newops", "password": "pass12345", "role": "technician"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201

        activity = _latest_activity("admin_user_created")
        assert activity is not None
        assert activity["entity_type"] == "user"
        assert activity["new_value"]["username"] == "newops"
