from __future__ import annotations

import logging
import re
from xml.sax.saxutils import escape

import httpx

from app.database import (
    clear_twilio_settings,
    create_voicemail_record,
    delete_voicemail_record,
    get_decrypted_twilio_auth_token,
    get_twilio_settings,
    get_voicemail_record,
    list_voicemail_records,
    update_twilio_settings,
    update_voicemail_record,
)

DEFAULT_VOICEMAIL_GREETING = (
    "Hi, and thank you for calling Tech Restore. "
    "We are helping customers right now. "
    "Please leave your name, phone number, and a short message. "
    "We will call you back as soon as we can."
)

DEFAULT_VOICEMAIL_TTS_VOICE = "Polly.Joanna"

logger = logging.getLogger(__name__)


class TwilioAudioFetchError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TwilioService:
    @staticmethod
    def get_settings() -> dict:
        return get_twilio_settings()

    @staticmethod
    def update_settings(payload: dict) -> dict:
        return update_twilio_settings(payload)

    @staticmethod
    def clear_settings() -> dict:
        return clear_twilio_settings()

    @staticmethod
    def list_voicemails() -> list[dict]:
        return list_voicemail_records()

    @staticmethod
    def get_voicemail(voicemail_id: int) -> dict | None:
        return get_voicemail_record(voicemail_id)

    @staticmethod
    def update_voicemail(voicemail_id: int, payload: dict) -> dict | None:
        return update_voicemail_record(voicemail_id, payload)

    @staticmethod
    def delete_voicemail(voicemail_id: int) -> bool:
        return delete_voicemail_record(voicemail_id)

    @staticmethod
    def create_voicemail(payload: dict) -> dict:
        return create_voicemail_record(payload)

    @staticmethod
    def get_setup_status() -> dict:
        settings = get_twilio_settings()
        public_base = settings.get("public_webhook_base_url")
        voice_webhook_url = TwilioService._build_callback_url(public_base, "/api/twilio/voice")
        recording_callback_url = TwilioService._build_callback_url(public_base, "/api/twilio/recording")
        last_voicemail = next(iter(list_voicemail_records()), None)
        return {
            "twilio_credentials_configured": bool(settings.get("configured")),
            "public_webhook_base_url_configured": bool(public_base),
            "voice_webhook_url": voice_webhook_url,
            "recording_callback_url": recording_callback_url,
            # This route is part of the active Twilio router and available whenever the API is up.
            "recording_callback_route_active": True,
            "last_voicemail": last_voicemail,
        }

    @staticmethod
    def build_voice_twiml(*, from_number: str | None, to_number: str | None) -> str:
        settings = get_twilio_settings()
        greeting = settings.get("voicemail_greeting") or DEFAULT_VOICEMAIL_GREETING
        greeting_audio_url = settings.get("voicemail_greeting_audio_url")
        recording_callback_url = TwilioService._build_callback_url(settings.get("public_webhook_base_url"), "/api/twilio/recording")
        greeting_block = TwilioService._build_greeting_prompt(greeting, greeting_audio_url)
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            f"{greeting_block}"
            "<Pause length=\"2\"/>"
            "<Record"
            " maxLength=\"120\""
            " timeout=\"5\""
            " playBeep=\"true\""
            " trim=\"trim-silence\""
            f" recordingStatusCallback=\"{escape(recording_callback_url)}\""
            " recordingStatusCallbackMethod=\"POST\""
            "/>"
            f"<Say voice=\"{DEFAULT_VOICEMAIL_TTS_VOICE}\">Thanks. We will call you back soon. Goodbye.</Say>"
            "</Response>"
        )

    @staticmethod
    def _build_greeting_prompt(greeting: str, greeting_audio_url: str | None) -> str:
        if isinstance(greeting_audio_url, str) and greeting_audio_url.strip():
            # Future-ready path for uploaded/recorded greetings once media management is added.
            return f"<Play>{escape(greeting_audio_url.strip())}</Play>"

        chunks = [item.strip() for item in re.split(r"[.!?]+", greeting) if item.strip()]
        if not chunks:
            chunks = [DEFAULT_VOICEMAIL_GREETING]

        parts: list[str] = []
        for index, chunk in enumerate(chunks):
            parts.append(f"<Say voice=\"{DEFAULT_VOICEMAIL_TTS_VOICE}\">{escape(chunk)}</Say>")
            if index < len(chunks) - 1:
                parts.append("<Pause length=\"1\"/>")
        return "".join(parts)

    @staticmethod
    def record_voice_callback(payload: dict) -> dict:
        recording_url = payload.get("RecordingUrl") or payload.get("recording_url")
        if recording_url and not recording_url.endswith(".mp3"):
            recording_url = f"{recording_url}.mp3"

        recording_duration = payload.get("RecordingDuration") or payload.get("recording_duration")
        duration_value = int(recording_duration) if str(recording_duration or "").strip().isdigit() else None

        record_payload = {
            "caller_number": payload.get("From") or payload.get("Caller") or payload.get("caller_number"),
            "called_number": payload.get("To") or payload.get("Called") or payload.get("called_number"),
            "call_sid": payload.get("CallSid") or payload.get("call_sid"),
            "recording_sid": payload.get("RecordingSid") or payload.get("recording_sid"),
            "recording_url": recording_url,
            "recording_duration_seconds": duration_value,
            "transcription_text": payload.get("TranscriptionText") or payload.get("transcription_text"),
            "notes": payload.get("notes"),
            "status": payload.get("status") or "new",
        }
        return create_voicemail_record(record_payload)

    @staticmethod
    def fetch_recording_audio(voicemail_id: int) -> tuple[bytes, str] | None:
        voicemail = get_voicemail_record(voicemail_id)
        if voicemail is None or not voicemail.get("recording_url"):
            return None

        account_sid, auth_token = TwilioService._get_credentials()
        if not account_sid or not auth_token:
            raise TwilioAudioFetchError("Twilio credentials are not configured for voicemail playback.", status_code=503)

        recording_url = voicemail["recording_url"]
        if not re.search(r"\.(mp3|wav|m4a)$", recording_url, re.IGNORECASE):
            recording_url = f"{recording_url}.mp3"

        response = TwilioService._request_recording_audio(recording_url, account_sid, auth_token)

        if response.status_code in (401, 403):
            raise TwilioAudioFetchError("Twilio denied access to the recording. Check Twilio credentials in Settings.", status_code=502)
        if response.status_code == 404:
            raise TwilioAudioFetchError("Recording is not ready yet. Try again in a few seconds.", status_code=503)
        if response.status_code >= 400:
            raise TwilioAudioFetchError("Could not load voicemail audio from Twilio.", status_code=502)

        content_type = response.headers.get("content-type", "audio/mpeg")
        return response.content, content_type

    @staticmethod
    def _request_recording_audio(recording_url: str, account_sid: str, auth_token: str) -> httpx.Response:
        client_kwargs = {
            "timeout": 15.0,
            "follow_redirects": True,
            "auth": (account_sid, auth_token),
        }

        try:
            with httpx.Client(**client_kwargs) as client:
                return client.get(recording_url)
        except httpx.TransportError as error:
            message = str(error)
            if "CERTIFICATE_VERIFY_FAILED" not in message:
                raise TwilioAudioFetchError("Could not connect to Twilio to load voicemail audio.", status_code=502) from error

            # Local Windows environments can miss issuer chains used by Twilio edge certs.
            logger.warning("Retrying Twilio recording fetch with SSL verification disabled")
            try:
                with httpx.Client(**client_kwargs, verify=False) as client:
                    return client.get(recording_url)
            except httpx.TransportError as retry_error:
                raise TwilioAudioFetchError("Could not establish a secure connection to Twilio recording storage.", status_code=502) from retry_error

    @staticmethod
    def _build_callback_url(base_url: str | None, path: str) -> str:
        if base_url:
            return f"{base_url.rstrip('/')}{path}"
        return path

    @staticmethod
    def _get_credentials() -> tuple[str | None, str | None]:
        settings = get_twilio_settings()
        account_sid = settings.get("account_sid")
        auth_token = get_decrypted_twilio_auth_token()
        return account_sid, auth_token
