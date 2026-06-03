from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app
from app.services.auth import AuthService
from app.services.emailer import EmailService


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

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_auth(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_auth_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)

    monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "1")
    monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
    monkeypatch.delenv("REPAIR_DESK_PASSWORD", raising=False)
    monkeypatch.setattr(EmailService, "send_invite_email", lambda **kwargs: None)

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


def _create_and_login(client: TestClient, role: str, prefix: str) -> tuple[dict, dict]:
    email = f"{prefix}.{role}@example.com"
    password = "password-123"
    username = f"{prefix}_{role}"
    AuthService.create_user(
        name=f"{prefix.title()} {role.title()}",
        email=email,
        username=username,
        password=password,
        role=role,
    )

    login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return ({"Authorization": f"Bearer {token}"}, login_resp.json()["user"])


class TestHealth:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {
            "service": "Tech Restore Desk API",
            "status": "ok",
        }

    def test_root_head_endpoint(self, client):
        response = client.head("/")
        assert response.status_code == 200
        assert response.text == ""

    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "Tech Restore Desk"
        assert "database_ready" in data
        assert "supported_model_count" in data
        assert "repair_category_count" in data


class TestCustomers:
    def test_create_customer(self, client):
        payload = {
            "full_name": "Test Customer",
            "primary_phone": "555-1234",
        }
        response = client.post("/api/customers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "Test Customer"
        assert data["primary_phone"] == "555-1234"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_customer_missing_phone(self, client):
        payload = {
            "full_name": "Test Customer",
        }
        response = client.post("/api/customers", json=payload)
        assert response.status_code == 422

    def test_list_customers(self, client):
        # Create a customer first
        payload = {
            "full_name": "List Test Customer",
            "primary_phone": "555-5678",
        }
        client.post("/api/customers", json=payload)
        
        response = client.get("/api/customers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestTickets:
    def test_create_ticket(self, client):
        # Create customer first
        customer_payload = {
            "full_name": "Ticket Test Customer",
            "primary_phone": "555-9999",
        }
        customer_resp = client.post("/api/customers", json=customer_payload)
        customer_id = customer_resp.json()["id"]

        # Create ticket
        ticket_payload = {
            "customer_id": customer_id,
            "issue_category": "Screen Replacement",
        }
        response = client.post("/api/tickets", json=ticket_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["issue_category"] == "Screen Replacement"
        assert data["status"] == "New Intake"
        assert "ticket_number" in data
        assert "id" in data

    def test_list_tickets(self, client):
        # Create customer and ticket
        customer_payload = {
            "full_name": "List Test Customer",
            "primary_phone": "555-2222",
        }
        customer_resp = client.post("/api/customers", json=customer_payload)
        customer_id = customer_resp.json()["id"]

        ticket_payload = {
            "customer_id": customer_id,
            "issue_category": "Battery",
        }
        client.post("/api/tickets", json=ticket_payload)

        response = client.get("/api/tickets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_tickets_paged(self, client):
        customer_payload = {
            "full_name": "Paged Ticket Customer",
            "primary_phone": "555-3434",
        }
        customer_resp = client.post("/api/customers", json=customer_payload)
        customer_id = customer_resp.json()["id"]

        client.post(
            "/api/tickets",
            json={
                "customer_id": customer_id,
                "issue_category": "Paged Check",
            },
        )

        response = client.get("/api/tickets/paged", params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        payload = response.json()
        assert payload["page"] == 1
        assert payload["page_size"] == 10
        assert payload["total"] >= 1
        assert isinstance(payload["items"], list)

    def test_get_ticket(self, client):
        # Create customer and ticket
        customer_payload = {
            "full_name": "Get Test Customer",
            "primary_phone": "555-3333",
        }
        customer_resp = client.post("/api/customers", json=customer_payload)
        customer_id = customer_resp.json()["id"]

        ticket_payload = {
            "customer_id": customer_id,
            "issue_category": "Charging Port",
        }
        ticket_resp = client.post("/api/tickets", json=ticket_payload)
        ticket_id = ticket_resp.json()["id"]

        response = client.get(f"/api/tickets/{ticket_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert data["customer_id"] == customer_id

    def test_close_ticket(self, client):
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Close Test Customer", "primary_phone": "555-1212"},
        )
        customer_id = customer_resp.json()["id"]

        ticket_resp = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Close Workflow"},
        )
        ticket_id = ticket_resp.json()["id"]

        close_resp = client.post(
            f"/api/tickets/{ticket_id}/close",
            json={"final_price": 89.5, "changed_by": "Alex", "note": "Closed at counter"},
        )
        assert close_resp.status_code == 200
        assert close_resp.json() == {
            "ticket_id": ticket_id,
            "status": "Picked Up / Closed",
            "closed": True,
        }

        ticket_get_resp = client.get(f"/api/tickets/{ticket_id}")
        assert ticket_get_resp.status_code == 200
        assert ticket_get_resp.json()["status"] == "Picked Up / Closed"


class TestTicketStatusTransitions:
    def _make_ticket(self, client) -> int:
        customer_id = client.post(
            "/api/customers",
            json={"full_name": "Status Test Customer", "primary_phone": "555-4444"},
        ).json()["id"]
        ticket_id = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Water Damage"},
        ).json()["id"]
        return ticket_id

    def _advance(self, client, ticket_id: int, new_status: str, extra: dict | None = None):
        payload = {"new_status": new_status, "changed_by": "Mattis"}
        if extra:
            payload.update(extra)
        return client.post(f"/api/tickets/{ticket_id}/status", json=payload)

    def test_update_ticket_status(self, client):
        ticket_id = self._make_ticket(client)
        response = self._advance(client, ticket_id, "Needs Diagnosis")
        assert response.status_code == 201
        data = response.json()
        assert data["new_status"] == "Needs Diagnosis"
        assert data["changed_by"] == "Mattis"
        assert "id" in data

    def test_invalid_transition_rejected(self, client):
        ticket_id = self._make_ticket(client)
        # Jump from New Intake directly to Ready for Pickup — not allowed
        response = self._advance(client, ticket_id, "Ready for Pickup")
        assert response.status_code == 422
        assert "Cannot move from" in response.json()["detail"]

    def test_unknown_status_rejected(self, client):
        ticket_id = self._make_ticket(client)
        response = self._advance(client, ticket_id, "Totally Made Up Status")
        assert response.status_code == 422
        assert "Unknown status" in response.json()["detail"]

    def test_happy_path_chain(self, client):
        ticket_id = self._make_ticket(client)
        chain = [
            "Needs Diagnosis",
            "Diagnosed",
            "Approved",
            "Ready for Repair",
            "In Repair",
        ]
        for status in chain:
            resp = self._advance(client, ticket_id, status)
            assert resp.status_code == 201, f"Failed to advance to '{status}': {resp.text}"

        # Ready for Pickup requires a final price
        resp = self._advance(client, ticket_id, "Ready for Pickup")
        assert resp.status_code == 422
        assert "final price" in resp.json()["detail"].lower()

        # Set final_price and retry
        resp = self._advance(client, ticket_id, "Ready for Pickup", {"final_price": 120.0})
        assert resp.status_code == 201
        assert resp.json()["new_status"] == "Ready for Pickup"


class TestLoaners:
    def test_create_checkout_and_return_loaner(self, client):
        loaner_code = f"L-{uuid4().hex[:8]}"
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Loaner Test Customer", "primary_phone": "555-7777"},
        )
        customer_id = customer_resp.json()["id"]

        ticket_resp = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Loaner Test Repair"},
        )
        ticket_id = ticket_resp.json()["id"]

        loaner_resp = client.post(
            "/api/loaners",
            json={"loaner_code": loaner_code, "model": "iPhone 8"},
        )
        assert loaner_resp.status_code == 201
        loaner_id = loaner_resp.json()["id"]

        checkout_resp = client.post(
            f"/api/loaners/{loaner_id}/checkout",
            json={"ticket_id": ticket_id, "customer_id": customer_id},
        )
        assert checkout_resp.status_code == 201
        checkout_data = checkout_resp.json()
        assert checkout_data["loaner_phone_id"] == loaner_id
        assert checkout_data["ticket_id"] == ticket_id
        assert checkout_data["status"] == "Checked Out"

        agreement_resp = client.get(f"/api/tickets/{ticket_id}/loaner-agreement")
        assert agreement_resp.status_code == 200
        agreement = agreement_resp.json()
        assert agreement["ticket_id"] == ticket_id
        assert agreement["loaner_phone_id"] == loaner_id
        assert agreement["loaner_code"] == loaner_code
        assert agreement["customer_name"] == "Loaner Test Customer"

        return_resp = client.post(
            f"/api/loaners/{loaner_id}/return",
            json={"return_staff": "Alex"},
        )
        assert return_resp.status_code == 200
        return_data = return_resp.json()
        assert return_data["loaner_phone_id"] == loaner_id
        assert return_data["status"] == "Returned"

        get_resp = client.get(f"/api/loaners/{loaner_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "Returned Needs Reset"


class TestHours:
    def test_create_list_and_summary_hours(self, client):
        create_resp = client.post(
            "/api/hours/",
            json={
                "technician": "Mattis",
                "work_date": "2026-05-10",
                "hours_worked": 2.5,
                "work_description": "Diagnostics and repair",
            },
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["technician"] == "Mattis"
        assert created["hours_worked"] == 2.5

        list_resp = client.get("/api/hours/", params={"technician": "Mattis"})
        assert list_resp.status_code == 200
        entries = list_resp.json()
        assert len(entries) >= 1
        assert entries[0]["technician"] == "Mattis"

        summary_resp = client.get(
            "/api/hours/summary",
            params={"start_date": "2026-05-10", "end_date": "2026-05-10", "technician": "Mattis"},
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["total_hours"] >= 2.5
        assert summary["by_technician"]["Mattis"] >= 2.5

    def test_clock_in_and_clock_out_hours(self, client):
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Clock Flow Customer", "primary_phone": "555-2020"},
        )
        customer_id = customer_resp.json()["id"]

        ticket_resp = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Battery swap"},
        )
        ticket_id = ticket_resp.json()["id"]

        clock_in_resp = client.post(
            "/api/hours/clock-in",
            json={"technician": "Mattis", "ticket_id": ticket_id, "work_description": "Bench diagnostics"},
        )
        assert clock_in_resp.status_code == 201
        session = clock_in_resp.json()
        assert session["technician"] == "Mattis"
        assert session["status"] == "active"
        assert session["ticket_id"] == ticket_id

        active_resp = client.get("/api/hours/active", params={"technician": "Mattis"})
        assert active_resp.status_code == 200
        active = active_resp.json()
        assert active["id"] == session["id"]
        assert active["status"] == "active"

        clock_out_resp = client.post(
            "/api/hours/clock-out",
            json={"technician": "Mattis"},
        )
        assert clock_out_resp.status_code == 200
        clocked_out = clock_out_resp.json()
        assert clocked_out["session"]["status"] == "completed"
        assert clocked_out["hours_entry"]["technician"] == "Mattis"
        assert clocked_out["hours_entry"]["ticket_id"] == ticket_id

        active_after_resp = client.get("/api/hours/active", params={"technician": "Mattis"})
        assert active_after_resp.status_code == 200
        assert active_after_resp.json() is None

    def test_date_filters_handle_datetime_like_work_date_values(self, client):
        create_resp = client.post(
            "/api/hours/",
            json={
                "technician": "Mattis",
                "work_date": "2026-05-27T13:20:00Z",
                "hours_worked": 1.3333333333,
                "work_description": "Date normalization regression test",
            },
        )
        assert create_resp.status_code == 201

        list_resp = client.get(
            "/api/hours/",
            params={"start_date": "2026-05-27", "end_date": "2026-05-27", "technician": "Mattis"},
        )
        assert list_resp.status_code == 200
        entries = list_resp.json()
        assert len(entries) >= 1
        assert all(item["work_date"] == "2026-05-27" for item in entries)

        summary_resp = client.get(
            "/api/hours/summary",
            params={"start_date": "2026-05-27", "end_date": "2026-05-27", "technician": "Mattis"},
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["total_hours"] >= 1.33


class TestDashboard:
    def test_summary_and_alerts(self, client):
        summary_resp = client.get("/api/dashboard/summary")
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert "open_tickets_count" in summary
        assert "checked_out_loaners_count" in summary
        assert "overdue_loaners_count" in summary

        alerts_resp = client.get("/api/dashboard/alerts")
        assert alerts_resp.status_code == 200
        alerts = alerts_resp.json()
        assert "summary" in alerts
        assert "overdue_items" in alerts
        assert isinstance(alerts["overdue_items"], list)


class TestReports:
    def test_report_summary_endpoint(self, client):
        report_day = datetime.now(UTC).date().isoformat()
        pricing_rules_resp = client.get("/api/pricing/rules")
        assert pricing_rules_resp.status_code == 200
        repair_category = pricing_rules_resp.json()["repair_categories"][0]

        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Reports Customer", "primary_phone": "555-8181"},
        )
        customer_id = customer_resp.json()["id"]

        ticket_resp = client.post(
            "/api/tickets",
            json={
                "customer_id": customer_id,
                "issue_category": "Reports Screen Repair",
                "assigned_technician": "Jordan",
            },
        )
        ticket_id = ticket_resp.json()["id"]

        repair_action_resp = client.post(
            f"/api/tickets/{ticket_id}/repair-actions",
            json={
                "repair_category_id": repair_category["id"],
                "action_description": "Screen assembly replacement",
                "part_cost": 50,
                "labor_minutes": 60,
                "difficulty_level": 2,
                "risk_level": 2,
                "performed_by": "Jordan",
            },
        )
        assert repair_action_resp.status_code == 201

        close_resp = client.post(
            f"/api/tickets/{ticket_id}/close",
            json={"final_price": 149.99, "changed_by": "Jordan"},
        )
        assert close_resp.status_code == 200

        hours_resp = client.post(
            "/api/hours/",
            json={
                "technician": "Jordan",
                "work_date": report_day,
                "hours_worked": 2.0,
                "work_description": "Closed ticket work",
                "ticket_id": ticket_id,
            },
        )
        assert hours_resp.status_code == 201

        summary_resp = client.get(
            "/api/reports/summary",
            params={
                "start_date": report_day,
                "end_date": report_day,
                "technician": "Jordan",
                "repair_category": repair_category["name"],
            },
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["created_tickets_count"] >= 1
        assert summary["closed_tickets_count"] >= 1
        assert summary["total_revenue"] >= 149.99
        assert summary["total_hours"] >= 2.0
        assert summary["revenue_per_hour"] > 0
        assert summary["technician_filter"] == "Jordan"
        assert summary["repair_category_filter"] == repair_category["name"]
        assert any(item["technician"] == "Jordan" for item in summary["technician_breakdown"])
        assert any(item["repair_category"] == repair_category["name"] for item in summary["repair_category_breakdown"])


class TestSystem:
    def test_backup_export_and_history(self, client):
        backup_resp = client.post("/api/system/backup")
        assert backup_resp.status_code == 200
        backup = backup_resp.json()
        assert backup["file_name"].endswith(".sqlite")

        export_resp = client.get("/api/system/export")
        assert export_resp.status_code == 200
        assert export_resp.headers["content-type"].startswith("application/json")

        history_resp = client.get("/api/system/history")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert any(item["activity_type"] == "backup" for item in history)
        assert any(item["activity_type"] == "export" for item in history)

    def test_get_and_patch_loaner_agreement_defaults(self, client):
        get_resp = client.get("/api/system/loaner-agreement-defaults")
        assert get_resp.status_code == 200
        defaults = get_resp.json()
        assert "responsibility_text" in defaults
        assert "return_policy_text" in defaults
        assert "signature_note_text" in defaults

        patch_resp = client.patch(
            "/api/system/loaner-agreement-defaults",
            json={
                "responsibility_text": "Borrower is responsible for device condition during checkout.",
            },
        )
        assert patch_resp.status_code == 200
        patched = patch_resp.json()
        assert patched["responsibility_text"].startswith("Borrower is responsible")

    def test_get_and_patch_notification_templates(self, client):
        get_resp = client.get("/api/system/notification-templates")
        assert get_resp.status_code == 200
        templates = get_resp.json()
        assert isinstance(templates, list)
        assert len(templates) >= 5
        
        template_keys = [t["template_key"] for t in templates]
        assert "diagnosis_complete" in template_keys
        assert "ready_for_pickup" in template_keys
        assert "waiting_for_parts" in template_keys
        assert "not_worth_repair" in template_keys
        assert "loaner_overdue" in template_keys

        # Update one template
        diagnosis_template = next(t for t in templates if t["template_key"] == "diagnosis_complete")
        patch_resp = client.patch(
            "/api/system/notification-templates",
            json={
                "diagnosis_complete": {
                    "template_text": "Your device [MODEL] has been diagnosed. Cost: $[AMOUNT]. Approve to proceed."
                }
            },
        )
        assert patch_resp.status_code == 200
        updated_templates = patch_resp.json()
        updated_diagnosis = next(t for t in updated_templates if t["template_key"] == "diagnosis_complete")
        assert "device [MODEL] has been diagnosed" in updated_diagnosis["template_text"]

    def test_audit_logs_and_query_metrics_endpoints(self, client):
        history_resp = client.get("/api/system/audit-logs", params={"page": 1, "page_size": 25})
        assert history_resp.status_code == 200
        history_payload = history_resp.json()
        assert history_payload["page"] == 1
        assert history_payload["page_size"] == 25
        assert "items" in history_payload
        assert "total" in history_payload

        metrics_resp = client.get("/api/system/performance/query-metrics")
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert "total_queries" in metrics
        assert "average_duration_ms" in metrics
        assert "top_slowest" in metrics

        reset_resp = client.post("/api/system/performance/query-metrics/reset")
        assert reset_resp.status_code == 200
        assert reset_resp.json()["reset"] is True


class TestQueue:
    def test_queue_endpoint_returns_grouped_statuses(self, client):
        queue_resp = client.get("/api/queue/")
        assert queue_resp.status_code == 200
        queue = queue_resp.json()
        assert "Loaner Outstanding" in queue
        assert "Waiting for Parts" in queue
        assert "Customer Approval Needed" in queue
        assert "New Intake" in queue
        assert "Needs Diagnosis" in queue


class TestInventory:
    def test_part_and_donor_workflows(self, client):
        part_number = f"P-TEST-{uuid4().hex[:8]}"
        device_identifier = f"D-TEST-{uuid4().hex[:8]}"
        part_resp = client.post(
            "/api/inventory/parts",
            json={
                "part_number": part_number,
                "part_name": "Test Screen",
                "category": "Screens",
                "quantity_on_hand": 0,
                "reorder_level": 5,
            },
        )
        assert part_resp.status_code == 201
        part = part_resp.json()
        part_id = part["id"]

        list_resp = client.get("/api/inventory/parts", params={"low_stock_only": True})
        assert list_resp.status_code == 200
        assert any(item["id"] == part_id for item in list_resp.json())

        get_resp = client.get(f"/api/inventory/parts/{part_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["part_number"] == part_number

        donor_resp = client.post(
            "/api/inventory/donors",
            json={"device_identifier": device_identifier, "device_model": "iPhone 8"},
        )
        assert donor_resp.status_code == 201
        donor_id = donor_resp.json()["id"]

        harvest_resp = client.post(
            f"/api/inventory/donors/{donor_id}/harvest",
            json={"part_id": part_id},
        )
        assert harvest_resp.status_code == 200
        assert harvest_resp.json()["id"] == donor_id

        update_resp = client.patch(
            f"/api/inventory/parts/{part_id}",
            json={"quantity_on_hand": 2},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["quantity_on_hand"] == 2

        movements_resp = client.get("/api/inventory/movements", params={"part_id": part_id})
        assert movements_resp.status_code == 200
        movements = movements_resp.json()
        assert movements["total"] >= 2
        movement_types = {item["movement_type"] for item in movements["items"]}
        assert "donor_harvest" in movement_types
        assert "adjust" in movement_types

        adjust_resp = client.post(
            f"/api/inventory/parts/{part_id}/adjust",
            json={"quantity_delta": -1, "movement_type": "correction", "reason": "cycle count correction"},
        )
        assert adjust_resp.status_code == 200
        assert adjust_resp.json()["quantity_on_hand"] == 1

        reconciliation_resp = client.post(
            "/api/inventory/reconciliation",
            json={
                "part_id": part_id,
                "actual_quantity": 4,
                "reason": "physical recount",
                "apply_adjustment": True,
                "resolved_by": "Ops Lead",
            },
        )
        assert reconciliation_resp.status_code == 201
        reconciliation = reconciliation_resp.json()
        assert reconciliation["part_id"] == part_id
        assert reconciliation["expected_quantity"] == 1
        assert reconciliation["actual_quantity"] == 4
        assert reconciliation["discrepancy"] == 3

        reconciliations_list = client.get("/api/inventory/reconciliation", params={"part_id": part_id})
        assert reconciliations_list.status_code == 200
        assert len(reconciliations_list.json()) >= 1


class TestSupportedModels:
    def test_supported_models_endpoint(self, client):
        response = client.get("/api/supported-models")
        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)
        assert len(models) > 0


class TestRepairCategories:
    def test_create_update_and_list_repair_categories(self, client):
        create_resp = client.post(
            "/api/repair-categories",
            json={
                "name": "Face ID calibration",
                "description": "Sensor and camera alignment workflow",
                "default_policy": "Advanced",
                "requires_soldering": False,
            },
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["name"] == "Face ID calibration"
        assert created["active"] is True

        patch_resp = client.patch(
            f"/api/repair-categories/{created['id']}",
            json={"active": False},
        )
        assert patch_resp.status_code == 200
        patched = patch_resp.json()
        assert patched["active"] is False

        active_list_resp = client.get("/api/repair-categories")
        assert active_list_resp.status_code == 200
        active_names = [item["name"] for item in active_list_resp.json()]
        assert "Face ID calibration" not in active_names

        full_list_resp = client.get("/api/repair-categories?include_inactive=true")
        assert full_list_resp.status_code == 200
        all_names = [item["name"] for item in full_list_resp.json()]
        assert "Face ID calibration" in all_names


class TestStatusWorkflowRules:
    def test_get_and_patch_status_workflow_rules(self, client):
        get_resp = client.get("/api/status-workflow")
        assert get_resp.status_code == 200
        rules = get_resp.json()
        assert "transitions" in rules
        assert "guardrails" in rules

        transitions = rules["transitions"]
        transitions["New Intake"] = ["Needs Diagnosis", "Diagnosed"]
        patch_resp = client.patch(
            "/api/status-workflow",
            json={
                "transitions": transitions,
                "guardrails": {
                    "enforce_final_price_for_ready_for_pickup": False,
                    "enforce_final_price_for_closed_paid_statuses": True,
                    "enforce_no_active_loaner_for_ready_for_pickup": True,
                    "enforce_no_active_loaner_for_closed_statuses": True,
                },
            },
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()
        assert "Diagnosed" in updated["transitions"]["New Intake"]
        assert updated["guardrails"]["enforce_final_price_for_ready_for_pickup"] is False

    def test_updated_workflow_rules_change_ticket_status_validation(self, client):
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Workflow Customer", "primary_phone": "555-1212"},
        )
        customer_id = customer_resp.json()["id"]
        ticket_resp = client.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Workflow test"},
        )
        ticket_id = ticket_resp.json()["id"]

        rules_resp = client.get("/api/status-workflow")
        rules = rules_resp.json()
        transitions = rules["transitions"]
        transitions["New Intake"] = ["Diagnosed"]
        client.patch("/api/status-workflow", json={"transitions": transitions})

        status_resp = client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"new_status": "Diagnosed", "changed_by": "Mattis"},
        )
        assert status_resp.status_code == 201
        assert status_resp.json()["new_status"] == "Diagnosed"


class TestPricing:
    def test_pricing_calculate_and_rules(self, client):
        calc_resp = client.post(
            "/api/pricing/calculate",
            json={
                "part_cost": 25,
                "labor_minutes": 30,
                "difficulty_level": 2,
                "risk_level": 1,
            },
        )
        assert calc_resp.status_code == 200
        calculation = calc_resp.json()
        assert "customer_price" in calculation
        assert "warnings" in calculation

        rules_resp = client.get("/api/pricing/rules")
        assert rules_resp.status_code == 200
        rules = rules_resp.json()
        assert "defaults" in rules
        assert "repair_categories" in rules

    def test_update_pricing_rules_applies_to_calculator_defaults(self, client):
        baseline_calc_resp = client.post(
            "/api/pricing/calculate",
            json={
                "part_cost": 0,
                "labor_minutes": 60,
                "difficulty_level": 1,
                "risk_level": 1,
            },
        )
        assert baseline_calc_resp.status_code == 200
        baseline_price = baseline_calc_resp.json()["customer_price"]

        update_resp = client.patch(
            "/api/pricing/rules",
            json={
                "base_labor_rate_per_hour": 90,
                "diagnostic_fee": 15,
            },
        )
        assert update_resp.status_code == 200
        updated_defaults = update_resp.json()["defaults"]
        assert updated_defaults["base_labor_rate_per_hour"] == 90
        assert updated_defaults["diagnostic_fee"] == 15

        rules_resp = client.get("/api/pricing/rules")
        assert rules_resp.status_code == 200
        rules = rules_resp.json()
        assert rules["defaults"]["base_labor_rate_per_hour"] == 90
        assert rules["defaults"]["diagnostic_fee"] == 15

        calc_resp = client.post(
            "/api/pricing/calculate",
            json={
                "part_cost": 0,
                "labor_minutes": 60,
                "difficulty_level": 1,
                "risk_level": 1,
            },
        )
        assert calc_resp.status_code == 200
        calculation = calc_resp.json()
        assert calculation["customer_price"] > baseline_price

    def test_pricing_catalog_crud_and_suggestion(self, client):
        catalog_resp = client.get("/api/pricing/catalog")
        assert catalog_resp.status_code == 200
        catalog = catalog_resp.json()
        assert len(catalog["brands"]) > 0
        assert len(catalog["models"]) > 0
        assert len(catalog["issue_types"]) > 0
        assert len(catalog["repair_types"]) > 0

        brand_resp = client.post("/api/pricing/catalog/brands", json={"name": "Test Brand"})
        assert brand_resp.status_code == 201
        brand_id = brand_resp.json()["id"]

        model_resp = client.post(
            "/api/pricing/catalog/models",
            json={"brand_id": brand_id, "name": "Model X"},
        )
        assert model_resp.status_code == 201
        model_id = model_resp.json()["id"]

        issue_resp = client.post(
            "/api/pricing/catalog/issue-types",
            json={"name": "Test Issue"},
        )
        assert issue_resp.status_code == 201
        issue_type_id = issue_resp.json()["id"]

        repair_resp = client.post(
            "/api/pricing/catalog/repair-types",
            json={"name": "Test Repair"},
        )
        assert repair_resp.status_code == 201
        repair_type_id = repair_resp.json()["id"]

        rule_resp = client.post(
            "/api/pricing/catalog/rules",
            json={
                "brand_id": brand_id,
                "model_id": model_id,
                "issue_type_id": issue_type_id,
                "repair_type_id": repair_type_id,
                "standard_price": 99,
                "estimated_part_cost": 15,
                "estimated_labor_minutes": 30,
                "customer_wording": "Standard quote",
                "internal_notes": "Internal test note",
            },
        )
        assert rule_resp.status_code == 201
        rule_id = rule_resp.json()["id"]

        suggest_resp = client.get(
            "/api/pricing/catalog/suggest",
            params={"brand": "Test Brand", "model": "Model X", "issue_type": "Test Issue"},
        )
        assert suggest_resp.status_code == 200
        suggest_payload = suggest_resp.json()
        assert suggest_payload["match_found"] is True
        assert suggest_payload["rule"]["id"] == rule_id

        update_resp = client.patch(
            f"/api/pricing/catalog/rules/{rule_id}",
            json={"active": False, "standard_price": 89},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["active"] is False
        assert update_resp.json()["standard_price"] == 89

        delete_resp = client.delete(f"/api/pricing/catalog/rules/{rule_id}")
        assert delete_resp.status_code == 204


class TestAuthAndPermissions:
    def test_owner_only_invites_enforced(self, client_auth):
        owner_headers, _ = _create_and_login(client_auth, "owner", "owner_inv")
        admin_headers, _ = _create_and_login(client_auth, "admin", "admin_inv")

        owner_create = client_auth.post(
            "/api/auth/invites",
            json={"email": "tech.a@example.com", "role": "technician", "name": "Tech A"},
            headers=owner_headers,
        )
        assert owner_create.status_code == 201

        admin_create = client_auth.post(
            "/api/auth/invites",
            json={"email": "tech.b@example.com", "role": "technician", "name": "Tech B"},
            headers=admin_headers,
        )
        assert admin_create.status_code == 403

    def test_invite_accept_cannot_be_reused(self, client_auth):
        owner_headers, _ = _create_and_login(client_auth, "owner", "owner_reuse")
        invite_resp = client_auth.post(
            "/api/auth/invites",
            json={"email": "reuse.user@example.com", "role": "viewer", "name": "Reuse User"},
            headers=owner_headers,
        )
        assert invite_resp.status_code == 201

        # Create an explicit token for acceptance checks.
        invite, raw_token = AuthService.create_invite(
            email="reuse.user@example.com",
            role="viewer",
            created_by=1,
            name="Reuse User",
            send_email=False,
        )
        assert invite["status"] == "pending"

        accept_resp = client_auth.post(
            f"/api/auth/invites/{raw_token}/accept",
            json={"password": "new-pass-123"},
        )
        assert accept_resp.status_code == 200

        accept_again = client_auth.post(
            f"/api/auth/invites/{raw_token}/accept",
            json={"password": "new-pass-123"},
        )
        assert accept_again.status_code == 400

    def test_pricing_write_restricted_to_owner_admin(self, client_auth):
        owner_headers, _ = _create_and_login(client_auth, "owner", "owner_price")
        tech_headers, _ = _create_and_login(client_auth, "technician", "tech_price")
        viewer_headers, _ = _create_and_login(client_auth, "viewer", "viewer_price")

        owner_patch = client_auth.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 25},
            headers=owner_headers,
        )
        assert owner_patch.status_code == 200

        tech_patch = client_auth.patch(
            "/api/pricing/rules",
            json={"diagnostic_fee": 35},
            headers=tech_headers,
        )
        assert tech_patch.status_code == 403

        viewer_read = client_auth.get("/api/pricing/catalog", headers=viewer_headers)
        assert viewer_read.status_code == 200

    def test_technician_can_create_ticket_viewer_cannot(self, client_auth):
        technician_headers, _ = _create_and_login(client_auth, "technician", "tech_ticket")
        viewer_headers, _ = _create_and_login(client_auth, "viewer", "viewer_ticket")

        customer_resp = client_auth.post(
            "/api/customers",
            json={"full_name": "Role Matrix", "primary_phone": "555-5151"},
            headers=technician_headers,
        )
        assert customer_resp.status_code == 201
        customer_id = customer_resp.json()["id"]

        ticket_resp = client_auth.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Technician Create"},
            headers=technician_headers,
        )
        assert ticket_resp.status_code == 201

        viewer_ticket_resp = client_auth.post(
            "/api/tickets",
            json={"customer_id": customer_id, "issue_category": "Viewer Create"},
            headers=viewer_headers,
        )
        assert viewer_ticket_resp.status_code == 403

    def test_change_password_requires_current_and_reauth(self, client_auth):
        headers, user = _create_and_login(client_auth, "admin", "admin_pwd")

        bad_current = client_auth.post(
            "/api/auth/change-password",
            json={
                "current_password": "wrong-pass",
                "new_password": "new-pass-123",
                "confirm_password": "new-pass-123",
            },
            headers=headers,
        )
        assert bad_current.status_code == 400

        good_change = client_auth.post(
            "/api/auth/change-password",
            json={
                "current_password": "password-123",
                "new_password": "new-pass-123",
                "confirm_password": "new-pass-123",
            },
            headers=headers,
        )
        assert good_change.status_code == 200

        old_login = client_auth.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "password-123"},
        )
        assert old_login.status_code == 401

        new_login = client_auth.post(
            "/api/auth/login",
            json={"email": user["email"], "password": "new-pass-123"},
        )
        assert new_login.status_code == 200
