from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import app.database as database
from app.main import app
from app.repositories.auth import AuthRepository
from app.utils.passwords import verify_password
from scripts.ensure_owner_account import OwnerSeedConfig, ensure_owner_account


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_owner_seed_test.sqlite"
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
    monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


def _config(email: str = "mattiskleinbh@gmail.com", password: str = "TR500tag") -> OwnerSeedConfig:
    return OwnerSeedConfig(
        email=email,
        password=password,
        name="Mattis Klein",
        username="techrestoreowner",
    )


def test_owner_recovery_script_creates_owner_when_missing(client):
    result = ensure_owner_account(_config())
    assert result.action == "created"

    user = AuthRepository.get_user_by_email("mattiskleinbh@gmail.com")
    assert user is not None
    assert user["role"] == "owner"
    assert user["status"] == "active"
    assert bool(user["is_active"]) is True



def test_owner_recovery_script_updates_existing_owner_without_duplicate(client):
    AuthRepository.create_user(
        name="Mattis Klein",
        email="mattiskleinbh@gmail.com",
        username="techrestoreowner",
        password_hash="invalid:hash",
        role="viewer",
        status="disabled",
        approved_by=None,
    )

    result = ensure_owner_account(_config(password="TR500tag"))
    assert result.action == "updated"

    users = [user for user in AuthRepository.list_users() if user["email"].lower() == "mattiskleinbh@gmail.com"]
    assert len(users) == 1
    user = users[0]
    assert user["role"] == "owner"
    assert user["status"] == "active"
    assert bool(user["is_active"]) is True
    assert verify_password("TR500tag", user["password_hash"]) is True



def test_seeded_owner_can_login_and_wrong_password_fails(client):
    ensure_owner_account(_config(password="TR500tag"))

    login_ok = client.post(
        "/api/auth/login",
        json={"email": "mattiskleinbh@gmail.com", "password": "TR500tag"},
    )
    assert login_ok.status_code == 200
    payload = login_ok.json()
    assert payload["user"]["role"] == "owner"
    assert payload["user"]["status"] == "active"
    assert payload["user"]["is_active"] is True

    login_bad = client.post(
        "/api/auth/login",
        json={"email": "mattiskleinbh@gmail.com", "password": "wrong-password"},
    )
    assert login_bad.status_code == 401
