import httpx
import pytest
from fastapi.testclient import TestClient
import base64
import hashlib

from twilio.request_validator import RequestValidator

import app.database as database
from app.main import app
from app.core.settings import get_settings
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
    monkeypatch.delenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", raising=False)
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "development")
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", "twilio-test-jwt-secret-minimum-length-stage2+")
    monkeypatch.setenv("TECH_RESTORE_SIGNED_URL_SECRET", "twilio-test-signed-secret-minimum-length-stage2+")
    monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "1")

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

        with database.get_connection() as connection:
            row = connection.execute(
                "SELECT auth_token_ciphertext FROM twilio_settings WHERE id = 1"
            ).fetchone()
        assert row is not None
        assert isinstance(row["auth_token_ciphertext"], str)
        assert row["auth_token_ciphertext"].startswith("v2:")

    def test_legacy_twilio_token_ciphertext_is_still_readable(self, client):
        database.update_twilio_settings(
            {
                "account_sid": "TWILIO_ACCOUNT_SID_LEGACY",
                "auth_token": "bootstrap-token",
                "phone_number": "+15555550199",
            }
        )

        secret = hashlib.sha256(get_settings().signed_url_secret.encode("utf-8")).digest()
        legacy_plaintext = "legacy-token-compat"
        encrypted = bytes(
            byte ^ secret[index % len(secret)] for index, byte in enumerate(legacy_plaintext.encode("utf-8"))
        )
        legacy_ciphertext = base64.urlsafe_b64encode(encrypted).decode("ascii")

        with database.get_connection() as connection:
            connection.execute(
                "UPDATE twilio_settings SET auth_token_ciphertext = ? WHERE id = 1",
                (legacy_ciphertext,),
            )
            connection.commit()

        assert database.get_decrypted_twilio_auth_token() == legacy_plaintext

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
    @staticmethod
    def _twilio_signature(url: str, form_data: dict[str, str], auth_token: str) -> str:
        validator = RequestValidator(auth_token)
        return validator.compute_signature(url, form_data)

    @staticmethod
    def _signed_post(client: TestClient, *, url_path: str, public_base: str, auth_token: str, data: dict[str, str]):
        full_url = f"{public_base.rstrip('/')}{url_path}"
        signature = TestTwilioWebhooks._twilio_signature(full_url, data, auth_token)
        return client.post(url_path, data=data, headers={"X-Twilio-Signature": signature})

    def test_voice_webhook_requires_valid_signature(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        body = {"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_001"}
        response = self._signed_post(
            client,
            url_path="/api/twilio/voice",
            public_base="https://api.example.com",
            auth_token="signature-token-stage2",
            data=body,
        )
        assert response.status_code == 200

    def test_market_sms_webhook_requires_valid_signature(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        body = {"From": "+15555550199", "Body": "HELP", "MessageSid": "SM_SIG_001"}
        response = self._signed_post(
            client,
            url_path="/api/market-updates/sms",
            public_base="https://api.example.com",
            auth_token="signature-token-stage2",
            data=body,
        )
        assert response.status_code == 200

    def test_recording_callback_requires_valid_signature(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        body = {
            "From": "+15555550999",
            "To": "+15555550100",
            "CallSid": "CA_SIG_REC_001",
            "RecordingSid": "RE_SIG_REC_001",
            "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC999/Recordings/RE_SIG_REC_001",
            "RecordingDuration": "20",
        }
        response = self._signed_post(
            client,
            url_path="/api/twilio/recording",
            public_base="https://api.example.com",
            auth_token="signature-token-stage2",
            data=body,
        )
        assert response.status_code == 200

    def test_missing_signature_is_rejected_and_has_no_side_effect(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        before = client.get("/api/voicemails")
        assert before.status_code == 200
        before_count = len(before.json())

        response = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550999",
                "To": "+15555550100",
                "CallSid": "CA_SIG_REC_002",
                "RecordingSid": "RE_SIG_REC_002",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC999/Recordings/RE_SIG_REC_002",
                "RecordingDuration": "20",
            },
        )
        assert response.status_code == 403

        after = client.get("/api/voicemails")
        assert after.status_code == 200
        assert len(after.json()) == before_count

    def test_forged_signature_is_rejected(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        response = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_003"},
            headers={"X-Twilio-Signature": "forged-signature"},
        )
        assert response.status_code == 403

    def test_signature_with_wrong_signed_url_is_rejected(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        body = {"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_004"}
        wrong_signature = self._twilio_signature(
            "https://api.other-example.com/api/twilio/voice",
            body,
            "signature-token-stage2",
        )
        response = client.post(
            "/api/twilio/voice",
            data=body,
            headers={"X-Twilio-Signature": wrong_signature},
        )
        assert response.status_code == 403

    def test_modified_form_fields_after_signing_are_rejected(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        original = {"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_005"}
        signature = self._twilio_signature(
            "https://api.example.com/api/twilio/voice",
            original,
            "signature-token-stage2",
        )
        tampered = dict(original)
        tampered["CallSid"] = "CA_SIG_005_TAMPERED"

        response = client.post(
            "/api/twilio/voice",
            data=tampered,
            headers={"X-Twilio-Signature": signature},
        )
        assert response.status_code == 403

    def test_proxy_public_url_reconstruction_uses_configured_public_base(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "0")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        body = {"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_006"}
        signature = self._twilio_signature(
            "https://api.example.com/api/twilio/voice",
            body,
            "signature-token-stage2",
        )

        response = client.post(
            "/api/twilio/voice",
            data=body,
            headers={
                "X-Twilio-Signature": signature,
                "X-Forwarded-Proto": "http",
                "X-Forwarded-Host": "attacker.example",
            },
        )
        assert response.status_code == 200

    def test_development_bypass_can_be_enabled_explicitly(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_APP_ENV", "development")
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "1")
        monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)

        response = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_BYPASS"},
        )
        assert response.status_code == 200

    def test_production_bypass_is_rejected(self, client, monkeypatch):
        monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
        monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", "prod-jwt-secret-minimum-length-stage2-checkpoint+")
        monkeypatch.setenv("TECH_RESTORE_SIGNED_URL_SECRET", "prod-signed-secret-minimum-length-stage2-check+")
        monkeypatch.setenv("TECH_RESTORE_TWILIO_SIGNATURE_BYPASS", "1")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "signature-token-stage2")

        response = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550155", "To": "+15555550100", "CallSid": "CA_SIG_BYPASS_PROD"},
            headers={"X-Twilio-Signature": "anything"},
        )
        assert response.status_code == 403
    def test_voice_webhook_returns_twiml(self, client):
        response = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550155", "To": "+15555550100", "CallSid": "CA123"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        assert "Tech Restore — your tech, restored" in response.text
        assert "For hours and location, press 1." in response.text
        assert "To leave us a message, press 2." in response.text
        assert "To speak with a technician, press 3." in response.text
        assert "/api/twilio/recording" in response.text
        assert "<Record" in response.text
        assert "Polly.Joanna" in response.text
        assert "<Pause" in response.text
        assert "transcribe=\"true\"" not in response.text

    def test_voice_menu_remains_public_when_auth_is_enabled(self, client, monkeypatch):
        from app.middleware import auth_gate

        monkeypatch.setattr(auth_gate, "auth_enforcement_enabled", lambda: True)

        response = client.post(
            "/api/twilio/voice/menu",
            data={"Digits": "2", "From": "+15555550155", "To": "+15555550100", "CallSid": "CA999"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        assert "After the tone, please leave a clear, detailed message" in response.text

    def test_voice_menu_option_1_returns_to_main_menu(self, client):
        response = client.post(
            "/api/twilio/voice/menu",
            data={"Digits": "1", "From": "+15555550155", "To": "+15555550100", "CallSid": "CA124"},
        )
        assert response.status_code == 200
        assert "500 West Kennedy Boulevard, in the back of the TAG office" in response.text
        assert "6 to 8 PM" in response.text
        assert "To return to the main menu, press 0." in response.text
        assert "<Gather numDigits=\"1\" action=\"/api/twilio/voice/menu\"" in response.text
        assert "<Redirect>/api/twilio/voice</Redirect>" in response.text

    def test_voice_menu_option_2_uses_normal_voicemail_prompt(self, client):
        response = client.post(
            "/api/twilio/voice/menu",
            data={"Digits": "2", "From": "+15555550155", "To": "+15555550100", "CallSid": "CA125"},
        )
        assert response.status_code == 200
        assert "After the tone, please leave a clear, detailed message with your name, phone number, which device you have, and a description of the issue you are experiencing." in response.text
        assert "We’ll get back to you as soon as possible, usually within 24 hours." in response.text
        assert "<Record" in response.text
        assert "/api/twilio/recording" in response.text

    def test_voice_menu_option_3_uses_live_call_prompt_and_25_second_timeout(self, client):
        monkeypatch = pytest.MonkeyPatch()
        try:
            monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")
            response = client.post(
                "/api/twilio/voice/menu",
                data={"Digits": "3", "From": "+15555550155", "To": "+15555550100", "CallSid": "CA126"},
            )
        finally:
            monkeypatch.undo()
        assert response.status_code == 200
        assert "Please hold while we connect you. You will hear ringing while we wait for a technician." in response.text
        assert "No technician is available right now. Please leave a message after the tone. We will return your call as soon as possible." in response.text
        assert "<Play loop=\"8\">https://api.twilio.com/cowbell.mp3</Play>" in response.text
        assert "<Record" in response.text

    def test_admin_sms_reply_only_consumes_pending_live_request(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")
        reply = TwilioService.handle_admin_live_sms_reply(
            from_number="+15555550199",
            message_body="accept",
        )
        assert reply is None

    def test_admin_sms_request_message_wording(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
        monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15555550100")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://example.ngrok.app")
        monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")

        request = database.create_live_call_request(
            {
                "call_sid": "CA_LIVE_010",
                "caller_number": "+15555550155",
                "admin_phone_number": "+15555550199",
                "timeout_seconds": 25,
            }
        )

        sent_messages: list[dict] = []

        class FakeHttpxClient:
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def post(self, url, data=None, **kwargs):
                sent_messages.append(data or {})
                class FakeResponse:
                    status_code = 201
                return FakeResponse()

        monkeypatch.setattr(httpx, "Client", FakeHttpxClient)

        TwilioService._send_live_call_request_sms(request)
        assert len(sent_messages) == 1
        assert "Incoming Tech Restore call from" in sent_messages[0]["Body"]
        assert "Reply accept to take the call, or decline to send the caller to voicemail." in sent_messages[0]["Body"]

    def test_admin_sms_reply_accepts_pending_live_call_request(self, client, monkeypatch):
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

    def test_admin_sms_reply_accepts_pending_live_call_request(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://example.ngrok.app")
        monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")

        database.create_live_call_request(
            {
                "call_sid": "CA_LIVE_001",
                "caller_number": "+15555550155",
                "admin_phone_number": "+15555550199",
                "timeout_seconds": 25,
            }
        )

        redirect_calls: list[dict] = []

        def fake_redirect_active_call(account_sid: str, auth_token: str, call_sid: str | None, callback_url: str):
            redirect_calls.append(
                {
                    "account_sid": account_sid,
                    "auth_token": auth_token,
                    "call_sid": call_sid,
                    "callback_url": callback_url,
                }
            )
            return {"sid": "CA_LIVE_001"}

        monkeypatch.setattr(TwilioService, "_redirect_active_call", staticmethod(fake_redirect_active_call))

        reply = TwilioService.handle_admin_live_sms_reply(
            from_number="+15555550199",
            message_body="accept",
        )

        assert reply is not None
        assert "accepted" in reply.lower()
        assert len(redirect_calls) == 1
        assert redirect_calls[0]["call_sid"] == "CA_LIVE_001"
        assert "/api/twilio/live-accept" in redirect_calls[0]["callback_url"]

        request = database.find_live_call_request_for_call_sid("CA_LIVE_001")
        assert request is not None
        assert request["status"] == "accepted"

    def test_admin_sms_reply_declines_pending_live_call_request(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://example.ngrok.app")
        monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")

        database.create_live_call_request(
            {
                "call_sid": "CA_LIVE_002",
                "caller_number": "+15555550155",
                "admin_phone_number": "+15555550199",
                "timeout_seconds": 25,
            }
        )

        redirect_calls: list[dict] = []

        def fake_redirect_active_call(account_sid: str, auth_token: str, call_sid: str | None, callback_url: str):
            redirect_calls.append(
                {
                    "account_sid": account_sid,
                    "auth_token": auth_token,
                    "call_sid": call_sid,
                    "callback_url": callback_url,
                }
            )
            return {"sid": "CA_LIVE_002"}

        monkeypatch.setattr(TwilioService, "_redirect_active_call", staticmethod(fake_redirect_active_call))

        reply = TwilioService.handle_admin_live_sms_reply(
            from_number="+15555550199",
            message_body="decline",
        )

        assert reply is not None
        assert reply == "Live technician request declined. Caller sent to voicemail."
        assert len(redirect_calls) == 1
        assert redirect_calls[0]["call_sid"] == "CA_LIVE_002"
        assert "/api/twilio/live-accept" in redirect_calls[0]["callback_url"]

        request = database.find_live_call_request_for_call_sid("CA_LIVE_002")
        assert request is not None
        assert request["status"] == "declined"

    def test_market_updates_sms_webhook_handles_live_call_admin_reply(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://example.ngrok.app")
        monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")

        database.create_live_call_request(
            {
                "call_sid": "CA_LIVE_003",
                "caller_number": "+15555550155",
                "admin_phone_number": "+15555550199",
                "timeout_seconds": 25,
            }
        )

        def fake_redirect_active_call(account_sid: str, auth_token: str, call_sid: str | None, callback_url: str):
            return {"sid": "CA_LIVE_003"}

        monkeypatch.setattr(TwilioService, "_redirect_active_call", staticmethod(fake_redirect_active_call))

        response = client.post(
            "/api/market-updates/sms",
            data={"From": "+15555550199", "Body": "ACCEPT", "MessageSid": "SM_LIVE"},
        )

        assert response.status_code == 200
        assert "<Message>" in response.text
        assert "accepted" in response.text.lower()

    def test_outbound_call_prompt_returns_twiml(self, client):
        response = client.get(
            "/api/twilio/outbound-call",
            params={"to_number": "+15555550987", "contact_name": "Sam Caller", "voicemail_id": 44},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/xml")
        assert "calling back about voicemail 44" in response.text
        assert "Please stay on the line while we connect you." in response.text

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

    def test_recording_callback_uses_voice_webhook_call_context_when_from_missing(self, client):
        voice_resp = client.post(
            "/api/twilio/voice",
            data={"From": "+15555550666", "To": "+15555550100", "CallSid": "CACTX1"},
        )
        assert voice_resp.status_code == 200

        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "unknown",
                "CallSid": "CACTX1",
                "RecordingSid": "RECTX1",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/ACCTX/Recordings/RECTX1",
                "RecordingDuration": "18",
            },
        )

        assert callback_resp.status_code == 200
        payload = callback_resp.json()
        assert payload["caller_number"] == "+15555550666"
        assert payload["called_number"] == "+15555550100"

    def test_recording_callback_sends_sms_alert_once_per_new_recording(self, client, monkeypatch):
        sent_alert_ids: list[int] = []

        def fake_send_alert(record: dict):
            sent_alert_ids.append(int(record["id"]))

        monkeypatch.setattr(TwilioService, "_send_new_voicemail_sms_alert", staticmethod(fake_send_alert))

        first_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550911",
                "To": "+15555550100",
                "CallSid": "CA911",
                "RecordingSid": "RE911",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC911/Recordings/RE911",
                "RecordingDuration": "20",
            },
        )
        assert first_resp.status_code == 200

        second_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550911",
                "To": "+15555550100",
                "CallSid": "CA911",
                "RecordingSid": "RE911",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC911/Recordings/RE911",
                "RecordingDuration": "21",
            },
        )
        assert second_resp.status_code == 200
        assert len(sent_alert_ids) == 1

    def test_recording_callback_trims_fields_and_ignores_blank_from(self, client):
        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "   ",
                "Caller": " +15555550801 ",
                "To": " +15555550100 ",
                "CallSid": " CA801 ",
                "RecordingSid": " RE801 ",
                "RecordingUrl": " https://api.twilio.com/2010-04-01/Accounts/AC801/Recordings/RE801 ",
                "RecordingDuration": " 9 ",
            },
        )
        assert callback_resp.status_code == 200
        payload = callback_resp.json()
        assert payload["caller_number"] == "+15555550801"
        assert payload["called_number"] == "+15555550100"
        assert payload["call_sid"] == "CA801"
        assert payload["recording_sid"] == "RE801"

    def test_recording_callback_falls_back_to_configured_line_when_to_missing(self, client):
        save_resp = client.put(
            "/api/settings/twilio",
            json={
                "account_sid": "TWILIO_ACCOUNT_SID_TEST_LINE",
                "auth_token": "line-token-123",
                "phone_number": "+18772683048",
            },
        )
        assert save_resp.status_code == 200

        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550888",
                "CallSid": "CA802",
                "RecordingSid": "RE802",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC802/Recordings/RE802",
                "RecordingDuration": "12",
            },
        )
        assert callback_resp.status_code == 200
        payload = callback_resp.json()
        assert payload["caller_number"] == "+15555550888"
        assert payload["called_number"] == "+18772683048"

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

    def test_voicemail_list_response_handles_null_phone_fields(self, client):
        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "CallSid": "CA803",
                "RecordingSid": "RE803",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC803/Recordings/RE803",
                "RecordingDuration": "5",
            },
        )
        assert callback_resp.status_code == 200

        inbox_resp = client.get("/api/voicemails")
        assert inbox_resp.status_code == 200
        record = next((vm for vm in inbox_resp.json() if vm["recording_sid"] == "RE803"), None)
        assert record is not None
        assert record["caller_number"] is None
        assert record["called_number"] is None

    def test_setup_status_uses_environment_webhook_base_and_credentials(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_FROM_ENV")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "env-secret")
        monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15550000001")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")

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

    def test_recording_callback_appends_mp3_extension_to_url(self, client):
        """RecordingUrl from Twilio arrives without file extension; backend must append .mp3 before saving."""
        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550222",
                "To": "+15555550100",
                "CallSid": "CA222",
                "RecordingSid": "RE222",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC222/Recordings/RE222",
                "RecordingDuration": "15",
            },
        )
        assert callback_resp.status_code == 200

        inbox_resp = client.get("/api/voicemails")
        assert inbox_resp.status_code == 200
        saved = next((vm for vm in inbox_resp.json() if vm["recording_sid"] == "RE222"), None)
        assert saved is not None
        assert saved["recording_url"].endswith(".mp3"), (
            "Recording URL must end with .mp3 so the backend can proxy the audio from Twilio"
        )

    def test_recording_callback_does_not_double_append_mp3(self, client):
        """If Twilio ever sends a URL already ending in .mp3, do not double-append."""
        callback_resp = client.post(
            "/api/twilio/recording",
            data={
                "From": "+15555550333",
                "To": "+15555550100",
                "CallSid": "CA333",
                "RecordingSid": "RE333",
                "RecordingUrl": "https://api.twilio.com/2010-04-01/Accounts/AC333/Recordings/RE333.mp3",
                "RecordingDuration": "8",
            },
        )
        assert callback_resp.status_code == 200
        inbox_resp = client.get("/api/voicemails")
        saved = next((vm for vm in inbox_resp.json() if vm["recording_sid"] == "RE333"), None)
        assert saved is not None
        assert saved["recording_url"] == "https://api.twilio.com/2010-04-01/Accounts/AC333/Recordings/RE333.mp3"

    def test_voicemail_audio_proxy_returns_correct_content_type(self, client, monkeypatch):
        """Audio proxy must forward the Twilio content-type header so the browser can decode the audio."""
        def fake_fetch(_: int):
            return b"fake-ogg-bytes", "audio/ogg"

        monkeypatch.setattr(TwilioService, "fetch_recording_audio", staticmethod(fake_fetch))
        response = client.get("/api/voicemails/1/audio")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/ogg")

    def test_voicemail_audio_proxy_returns_404_when_no_recording_url(self, client, monkeypatch):
        """If the voicemail record has no recording_url, fetch_recording_audio returns None → 404."""
        monkeypatch.setattr(TwilioService, "fetch_recording_audio", staticmethod(lambda _: None))
        response = client.get("/api/voicemails/9999/audio")
        assert response.status_code == 404

    def test_alert_destination_number_returns_none_when_not_configured(self, client, monkeypatch):
        monkeypatch.delenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", raising=False)
        result = TwilioService._alert_destination_number()
        assert result is None, "No hardcoded phone number fallback should exist"

    def test_press_3_routes_to_voicemail_when_alert_to_not_configured(self, client):
        response = client.post(
            "/api/twilio/voice/menu",
            data={"Digits": "3", "From": "+15555550155", "To": "+15555550100", "CallSid": "CA_NO_ENV"},
        )
        assert response.status_code == 200
        assert "<Record" in response.text

    def test_accept_and_decline_are_case_insensitive(self, client, monkeypatch):
        monkeypatch.setenv("TWILIO_NEW_VOICEMAIL_ALERT_TO", "+15555550199")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
        monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://example.ngrok.app")

        database.create_live_call_request(
            {
                "call_sid": "CA_CASE_01",
                "caller_number": "+15555550155",
                "admin_phone_number": "+15555550199",
                "timeout_seconds": 25,
            }
        )
        monkeypatch.setattr(
            TwilioService,
            "_redirect_active_call",
            staticmethod(lambda *a, **kw: {"sid": "CA_CASE_01"}),
        )
        reply = TwilioService.handle_admin_live_sms_reply(
            from_number="+15555550199", message_body="Accept"
        )
        assert reply is not None and "accepted" in reply.lower()

        database.create_live_call_request(
            {
                "call_sid": "CA_CASE_02",
                "caller_number": "+15555550155",
                "admin_phone_number": "+15555550199",
                "timeout_seconds": 25,
            }
        )
        reply = TwilioService.handle_admin_live_sms_reply(
            from_number="+15555550199", message_body="Decline"
        )
        assert reply is not None and "declined" in reply.lower()

