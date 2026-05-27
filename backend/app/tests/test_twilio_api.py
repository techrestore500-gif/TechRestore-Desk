import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app
from app.services.twilio import TwilioAudioFetchError, TwilioService


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_desk_twilio_test.sqlite"
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


class TestTwilioSettings:
    def test_save_and_load_settings_without_leaking_auth_token(self, client):
        put_resp = client.put(
            "/api/settings/twilio",
            json={
                "account_sid": "TWILIO_ACCOUNT_SID_TEST_1",
                "auth_token": "secret-token-123",
                "phone_number": "+15555550100",
                "public_webhook_base_url": "https://example.ngrok.app",
                "voicemail_greeting": "Hello from Tech Restore",
            },
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["twilio_auth_token_set"] is True

        get_resp = client.get("/api/settings/twilio")
        assert get_resp.status_code == 200
        payload = get_resp.json()
        assert payload["account_sid"] == "TWILIO_ACCOUNT_SID_TEST_1"
        assert payload["phone_number"] == "+15555550100"
        assert payload["twilio_auth_token_set"] is True
        assert payload["configured"] is True
        assert "secret-token-123" not in get_resp.text
        assert "auth_token" not in payload

    def test_clear_settings(self, client):
        client.put(
            "/api/settings/twilio",
            json={
                "account_sid": "TWILIO_ACCOUNT_SID_TEST_2",
                "auth_token": "another-secret",
                "phone_number": "+15555550101",
            },
        )

        delete_resp = client.delete("/api/settings/twilio")
        assert delete_resp.status_code == 200
        payload = delete_resp.json()
        assert payload["twilio_auth_token_set"] is False
        assert payload["configured"] is False


class TestTwilioWebhooks:
    def test_voice_webhook_returns_twiml(self, client):
        response = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550155", "To": "+15555550100", "CallSid": "CA123"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        assert "Tech Restore" in response.text
        assert "/api/twilio/recording" in response.text
        assert "<Record" in response.text
        assert "Polly.Joanna" in response.text
        assert "<Pause" in response.text
        assert "transcribe=\"true\"" not in response.text

    def test_voice_webhook_prefers_play_when_audio_greeting_url_is_set(self, client):
        save_resp = client.put(
            "/api/settings/twilio",
            json={
                "account_sid": "TWILIO_ACCOUNT_SID_TEST_1",
                "auth_token": "secret-token-123",
                "phone_number": "+15555550100",
                "voicemail_greeting_audio_url": "https://cdn.example.com/greeting.mp3",
            },
        )
        assert save_resp.status_code == 200

        response = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550155", "To": "+15555550100", "CallSid": "CA124"},
        )
        assert response.status_code == 200
        assert "<Play>https://cdn.example.com/greeting.mp3</Play>" in response.text

    def test_recording_callback_creates_voicemail_record(self, client):
        customer_resp = client.post(
            "/api/customers",
            json={"full_name": "Voicemail Customer", "primary_phone": "+15555550999"},
        )
        assert customer_resp.status_code == 201

        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550999",
                "To": "+15555550100",
                "CallSid": "CA999",
                "RecordingSid": "RE999",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC999/Recordings/RE999",
                "RecordingDuration": "37",
                "TranscriptionText": "Please call me back.",
            },
        )
        assert callback_resp.status_code == 200
        record = callback_resp.json()
        assert record["caller_number"] == "+15555550999"
        assert record["recording_duration_seconds"] == 37
        assert record["customer_name"] == "Voicemail Customer"
        assert record["status"] == "new"

        inbox_resp = client.get("/api/voicemails")
        assert inbox_resp.status_code == 200
        inbox = inbox_resp.json()
        assert len(inbox) == 1
        assert inbox[0]["recording_sid"] == "RE999"
        assert inbox[0]["customer_phone"] == "+15555550999"

    def test_recording_callback_uses_caller_called_when_from_to_missing(self, client):
        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "Caller": "+15555550777",
                "Called": "+15555550100",
                "CallSid": "CA101",
                "RecordingSid": "RE101",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC101/Recordings/RE101",
                "RecordingDuration": "14",
            },
        )
        assert callback_resp.status_code == 200
        payload = callback_resp.json()
        assert payload["caller_number"] == "+15555550777"
        assert payload["called_number"] == "+15555550100"

    def test_voicemail_patch_updates_status_and_notes(self, client):
        created = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550123",
                "To": "+15555550100",
                "CallSid": "CA777",
                "RecordingSid": "RE777",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC777/Recordings/RE777",
                "RecordingDuration": "21",
            },
        ).json()

        patch_resp = client.patch(
            f"/api/voicemails/{created['id']}",
            json={"status": "listened", "note": "Called back later today"},
        )
        assert patch_resp.status_code == 200
        payload = patch_resp.json()
        assert payload["status"] == "listened"
        assert "Called back later today" in (payload["notes"] or "")

    def test_voicemail_delete_removes_message(self, client):
        created = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550123",
                "To": "+15555550100",
                "CallSid": "CA778",
                "RecordingSid": "RE778",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC778/Recordings/RE778",
                "RecordingDuration": "19",
            },
        ).json()

        delete_resp = client.delete(f"/api/voicemails/{created['id']}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted"] is True

        inbox_resp = client.get("/api/voicemails")
        assert inbox_resp.status_code == 200
        assert len(inbox_resp.json()) == 0

    def test_setup_status_returns_last_voicemail(self, client):
        client.put(
            "/api/settings/twilio",
            json={
                "account_sid": "TWILIO_ACCOUNT_SID_TEST_3",
                "auth_token": "status-token",
                "phone_number": "+15555550155",
                "public_webhook_base_url": "https://example.ngrok.app",
                "voicemail_greeting": "Please leave a message",
            },
        )
        client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550888",
                "To": "+15555550155",
                "CallSid": "CA888",
                "RecordingSid": "RE888",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC888/Recordings/RE888",
                "RecordingDuration": "11",
            },
        )

        response = client.get("/api/settings/twilio/setup-status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["twilio_credentials_configured"] is True
        assert payload["public_webhook_base_url_configured"] is True
        assert payload["voice_webhook_url"] == "https://example.ngrok.app/api/twilio/voice"
        assert payload["recording_callback_url"] == "https://example.ngrok.app/api/twilio/recording"
        assert payload["recording_callback_route_active"] is True
        assert payload["last_voicemail"]["recording_sid"] == "RE888"

    def test_setup_status_uses_environment_webhook_base_and_credentials(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_FROM_ENV")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "env-secret")
        monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15550000001")
        monkeypatch.setenv("PUBLIC_BASE_URL", "https://api.example.com")

        response = client.get("/api/settings/twilio/setup-status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["twilio_credentials_configured"] is True
        assert payload["public_webhook_base_url_configured"] is True
        assert payload["voice_webhook_url"] == "https://api.example.com/api/twilio/voice"
        assert payload["recording_callback_url"] == "https://api.example.com/api/twilio/recording"

    def test_voicemail_audio_proxy_returns_audio_bytes(self, client, monkeypatch):
        def fake_fetch(_: int):
            return b"audio-bytes", "audio/mpeg"

        monkeypatch.setattr(TwilioService, "fetch_recording_audio", staticmethod(fake_fetch))
        response = client.get("/api/voicemails/1/audio")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/mpeg")
        assert response.content == b"audio-bytes"

    def test_voicemail_audio_proxy_maps_fetch_error_to_http_error(self, client, monkeypatch):
        def fake_fetch(_: int):
            raise TwilioAudioFetchError("Recording is not ready yet. Try again in a few seconds.", status_code=503)

        monkeypatch.setattr(TwilioService, "fetch_recording_audio", staticmethod(fake_fetch))
        response = client.get("/api/voicemails/1/audio")
        assert response.status_code == 503
        assert response.json()["detail"] == "Recording is not ready yet. Try again in a few seconds."
