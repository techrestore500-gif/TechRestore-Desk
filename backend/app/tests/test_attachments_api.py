from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app
from app.services import attachments as attachment_service

PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"
    attachment_root = tmp_path / "attachments"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)

    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_LOCAL_ROOT", str(attachment_root))
    monkeypatch.setenv("TECH_RESTORE_ATTACHMENTS_PROVIDER", "local")
    monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "1")

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


def _create_ticket(client: TestClient) -> int:
    customer_resp = client.post(
        "/api/customers",
        json={"full_name": "Attachment Test", "primary_phone": "555-0000"},
    )
    assert customer_resp.status_code == 201
    customer_id = customer_resp.json()["id"]

    ticket_resp = client.post(
        "/api/tickets",
        json={"customer_id": customer_id, "issue_category": "Attachment Intake"},
    )
    assert ticket_resp.status_code == 201
    return int(ticket_resp.json()["id"])


def test_ticket_attachment_upload_signed_download_and_delete(client: TestClient, tmp_path):
    ticket_id = _create_ticket(client)

    upload_resp = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        params={"attachment_type": "intake_photo"},
        files={"file": ("intake.png", PNG_BYTES, "image/png")},
    )
    assert upload_resp.status_code == 201
    attachment = upload_resp.json()
    assert attachment["entity_type"] == "ticket"
    assert attachment["entity_id"] == ticket_id
    assert attachment["mime_type"] == "image/png"
    assert attachment["file_size"] == len(PNG_BYTES)

    list_resp = client.get(f"/api/tickets/{ticket_id}/attachments")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["id"] == attachment["id"]

    signed_resp = client.post(f"/api/attachments/{attachment['id']}/signed-url")
    assert signed_resp.status_code == 200
    signed = signed_resp.json()
    assert signed["url"].startswith("/api/attachments/download/")

    download_resp = client.get(signed["url"])
    assert download_resp.status_code == 200
    assert download_resp.content == PNG_BYTES
    assert download_resp.headers["content-type"].startswith("image/png")

    delete_resp = client.delete(f"/api/attachments/{attachment['id']}")
    assert delete_resp.status_code == 200

    after_list = client.get(f"/api/tickets/{ticket_id}/attachments")
    assert after_list.status_code == 200
    assert after_list.json() == []


def test_upload_validation_rejects_unsupported_mime(client: TestClient):
    ticket_id = _create_ticket(client)

    response = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        params={"attachment_type": "invoice"},
        files={"file": ("invoice.txt", b"plain-text", "text/plain")},
    )

    assert response.status_code == 400
    assert "MIME" in response.json()["detail"]


def test_signed_url_requires_auth_when_bypass_disabled(client: TestClient, monkeypatch):
    ticket_id = _create_ticket(client)
    upload_resp = client.post(
        f"/api/tickets/{ticket_id}/attachments",
        params={"attachment_type": "intake_photo"},
        files={"file": ("intake.png", PNG_BYTES, "image/png")},
    )
    attachment_id = upload_resp.json()["id"]

    monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")
    response = client.post(f"/api/attachments/{attachment_id}/signed-url")
    assert response.status_code == 401


def test_cleanup_orphans_removes_unlinked_files(client: TestClient, tmp_path):
    root = tmp_path / "attachments"
    orphan_path = root / "ticket" / "999" / f"orphan-{uuid4().hex}.png"
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_bytes(PNG_BYTES)

    response = client.post("/api/attachments/cleanup-orphans", params={"prefix": "ticket/999"})
    assert response.status_code == 200
    data = response.json()
    assert data["deleted_count"] == 1
    assert len(data["deleted_keys"]) == 1
    assert not orphan_path.exists()


def test_upload_failure_does_not_create_attachment_metadata(client: TestClient, monkeypatch):
    ticket_id = _create_ticket(client)

    class FailingProvider:
        def put_object(self, *, key: str, content: bytes, content_type: str) -> None:
            raise RuntimeError("disk write failed")

        def get_object(self, *, key: str):
            raise FileNotFoundError

        def delete_object(self, *, key: str) -> None:
            return None

        def object_exists(self, *, key: str) -> bool:
            return False

        def iter_keys(self, *, prefix: str = "") -> list[str]:
            return []

    monkeypatch.setattr(attachment_service, "build_storage_provider", lambda _settings: FailingProvider())

    before_count = len(database.list_attachments_for_entity("ticket", ticket_id))
    with pytest.raises(RuntimeError):
        client.post(
            f"/api/tickets/{ticket_id}/attachments",
            params={"attachment_type": "intake_photo"},
            files={"file": ("intake.png", PNG_BYTES, "image/png")},
        )

    after_count = len(database.list_attachments_for_entity("ticket", ticket_id))
    assert after_count == before_count
