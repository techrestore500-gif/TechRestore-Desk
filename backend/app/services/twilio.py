from __future__ import annotations

import logging
import os
import re
import time
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
    "Thank you for calling Tech Restore at 500 West Kennedy Boulevard. "
    "Please leave a detailed message with your name, phone number, which device you have, "
    "and a description of the issue you are experiencing. "
    "A technician is usually available between 4 PM and 5 PM daily, "
    "and we will get back to you within 24 hours. "
    "Thank you!"
)

DEFAULT_VOICEMAIL_TTS_VOICE = "Polly.Joanna"
DEFAULT_NEW_VOICEMAIL_ALERT_TO = "+18483291230"
NEW_VOICEMAIL_ALERT_TO_ENV = "TWILIO_NEW_VOICEMAIL_ALERT_TO"
CALL_CONTEXT_TTL_SECONDS = 6 * 60 * 60
MAX_CALL_CONTEXT_ENTRIES = 500

UNKNOWN_CALLER_VALUES = {
    "unknown",
    "anonymous",
    "private",
    "restricted",
    "unavailable",
    "client:unknown",
}

logger = logging.getLogger(__name__)

_recent_call_context: dict[str, tuple[float, str | None, str | None]] = {}


class TwilioAudioFetchError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TwilioService:
    @staticmethod
    def _first_non_empty(*values: str | None) -> str | None:
        for value in values:
            if value is None:
                continue
            candidate = value.strip()
            if candidate:
                return candidate
        return None

    @staticmethod
    def _public_webhook_base_from_env() -> str | None:
        return (
            TwilioService._clean_env("PUBLIC_WEBHOOK_BASE_URL")
            or TwilioService._clean_env("PUBLIC_API_BASE_URL")
            or TwilioService._clean_env("PUBLIC_BASE_URL")
        )

    @staticmethod
    def remember_voice_call_context(call_sid: str | None, from_number: str | None, to_number: str | None) -> None:
        call_sid_value = TwilioService._first_non_empty(call_sid)
        if not call_sid_value:
            return

        normalized_from = TwilioService._normalize_party_number(from_number)
        normalized_to = TwilioService._normalize_party_number(to_number)
        _recent_call_context[call_sid_value] = (time.time(), normalized_from, normalized_to)
        TwilioService._prune_recent_call_context()

    @staticmethod
    def _prune_recent_call_context() -> None:
        now = time.time()
        expired = [call_sid for call_sid, (seen_at, _, _) in _recent_call_context.items() if now - seen_at > CALL_CONTEXT_TTL_SECONDS]
        for call_sid in expired:
            _recent_call_context.pop(call_sid, None)

        overflow = len(_recent_call_context) - MAX_CALL_CONTEXT_ENTRIES
        if overflow <= 0:
            return

        oldest_call_sids = sorted(_recent_call_context.items(), key=lambda item: item[1][0])[:overflow]
        for call_sid, _ in oldest_call_sids:
            _recent_call_context.pop(call_sid, None)

    @staticmethod
    def _find_recent_call_context(call_sid: str | None) -> tuple[str | None, str | None]:
        call_sid_value = TwilioService._first_non_empty(call_sid)
        if not call_sid_value:
            return None, None

        context = _recent_call_context.get(call_sid_value)
        if context is None:
            return None, None

        seen_at, from_number, to_number = context
        if time.time() - seen_at > CALL_CONTEXT_TTL_SECONDS:
            _recent_call_context.pop(call_sid_value, None)
            return None, None
        return from_number, to_number

    @staticmethod
    def get_settings() -> dict:
        settings = get_twilio_settings()
        env_account_sid = TwilioService._clean_env("TWILIO_ACCOUNT_SID")
        env_phone_number = TwilioService._clean_env("TWILIO_PHONE_NUMBER")
        env_public_base_url = TwilioService._public_webhook_base_from_env()
        env_auth_token = TwilioService._clean_env("TWILIO_AUTH_TOKEN")

        if env_account_sid:
            settings["account_sid"] = env_account_sid
        if env_phone_number:
            settings["phone_number"] = env_phone_number
        if env_public_base_url:
            settings["public_webhook_base_url"] = env_public_base_url
        if env_auth_token:
            settings["twilio_auth_token_set"] = True

        settings["configured"] = bool(settings.get("account_sid") and settings.get("twilio_auth_token_set"))
        return settings

    @staticmethod
    def update_settings(payload: dict) -> dict:
        update_twilio_settings(payload)
        return TwilioService.get_settings()

    @staticmethod
    def clear_settings() -> dict:
        clear_twilio_settings()
        return TwilioService.get_settings()

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
        settings = TwilioService.get_settings()
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
        settings = TwilioService.get_settings()
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
        recording_url = TwilioService._first_non_empty(payload.get("RecordingUrl"), payload.get("recording_url"))
        if recording_url and not recording_url.endswith(".mp3"):
            recording_url = f"{recording_url}.mp3"

        settings = TwilioService.get_settings()

        call_sid = TwilioService._first_non_empty(payload.get("CallSid"), payload.get("call_sid"))
        recording_duration = TwilioService._first_non_empty(payload.get("RecordingDuration"), payload.get("recording_duration"))
        duration_value = int(recording_duration) if str(recording_duration or "").strip().isdigit() else None

        recording_sid = TwilioService._first_non_empty(payload.get("RecordingSid"), payload.get("recording_sid"))
        existing_record = TwilioService._find_existing_voicemail_by_recording_sid(recording_sid)

        caller_number = TwilioService._normalize_party_number(TwilioService._first_non_empty(
            payload.get("From"),
            payload.get("Caller"),
            payload.get("caller_number"),
        ))
        called_number = TwilioService._normalize_party_number(TwilioService._first_non_empty(
            payload.get("To"),
            payload.get("Called"),
            payload.get("called_number"),
            settings.get("phone_number"),
            TwilioService._clean_env("TWILIO_PHONE_NUMBER"),
        ))

        recent_from, recent_to = TwilioService._find_recent_call_context(call_sid)
        if caller_number is None:
            caller_number = recent_from
        if called_number is None:
            called_number = recent_to

        if caller_number is None or called_number is None:
            fetched_from, fetched_to = TwilioService._fetch_call_participants(call_sid)
            if caller_number is None:
                caller_number = fetched_from
            if called_number is None:
                called_number = fetched_to

        record_payload = {
            "caller_number": caller_number,
            "called_number": called_number,
            "call_sid": call_sid,
            "recording_sid": recording_sid,
            "recording_url": recording_url,
            "recording_duration_seconds": duration_value,
            "transcription_text": TwilioService._first_non_empty(payload.get("TranscriptionText"), payload.get("transcription_text")),
            "notes": TwilioService._first_non_empty(payload.get("notes")),
            "status": TwilioService._first_non_empty(payload.get("status")) or "new",
        }
        record = create_voicemail_record(record_payload)

        if existing_record is None:
            TwilioService._send_new_voicemail_sms_alert(record)

        return record

    @staticmethod
    def _find_existing_voicemail_by_recording_sid(recording_sid: str | None) -> dict | None:
        if not recording_sid:
            return None
        for voicemail in list_voicemail_records():
            if voicemail.get("recording_sid") == recording_sid:
                return voicemail
        return None

    @staticmethod
    def _normalize_party_number(value: str | None) -> str | None:
        candidate = TwilioService._first_non_empty(value)
        if candidate is None:
            return None
        if candidate.lower() in UNKNOWN_CALLER_VALUES:
            return None
        digits = re.sub(r"\D", "", candidate)
        if not digits and candidate.lower().startswith("client:"):
            return None
        return candidate

    @staticmethod
    def _fetch_call_participants(call_sid: str | None) -> tuple[str | None, str | None]:
        if not call_sid:
            return None, None

        account_sid, auth_token = TwilioService._get_credentials()
        if not account_sid or not auth_token:
            return None, None

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
        try:
            with httpx.Client(timeout=10.0, auth=(account_sid, auth_token)) as client:
                response = client.get(url)
        except httpx.TransportError:
            return None, None

        if response.status_code >= 400:
            return None, None

        try:
            payload = response.json()
        except ValueError:
            return None, None

        return (
            TwilioService._normalize_party_number(TwilioService._first_non_empty(payload.get("from"))),
            TwilioService._normalize_party_number(TwilioService._first_non_empty(payload.get("to"))),
        )

    @staticmethod
    def _alert_destination_number() -> str:
        return TwilioService._clean_env(NEW_VOICEMAIL_ALERT_TO_ENV) or DEFAULT_NEW_VOICEMAIL_ALERT_TO

    @staticmethod
    def _send_new_voicemail_sms_alert(record: dict) -> None:
        account_sid, auth_token = TwilioService._get_credentials()
        if not account_sid or not auth_token:
            return

        from_number = TwilioService._first_non_empty(
            TwilioService._clean_env("TWILIO_PHONE_NUMBER"),
            TwilioService.get_settings().get("phone_number"),
        )
        if not from_number:
            return

        to_number = TwilioService._alert_destination_number()
        caller = TwilioService._first_non_empty(record.get("caller_number")) or "Unknown"
        line = TwilioService._first_non_empty(record.get("called_number")) or "Unknown"
        duration_seconds = record.get("recording_duration_seconds")
        duration_text = f"{duration_seconds}s" if isinstance(duration_seconds, int) and duration_seconds >= 0 else "unknown"
        voicemail_id = record.get("id")

        body = (
            "New Tech Restore voicemail"
            f" | From: {caller}"
            f" | Line: {line}"
            f" | Duration: {duration_text}"
            f" | ID: {voicemail_id}"
        )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        try:
            with httpx.Client(timeout=10.0, auth=(account_sid, auth_token)) as client:
                response = client.post(
                    url,
                    data={
                        "From": from_number,
                        "To": to_number,
                        "Body": body,
                    },
                )
            if response.status_code >= 400:
                logger.warning("Failed to send voicemail SMS alert: HTTP %d", response.status_code)
        except httpx.TransportError as error:
            logger.warning("Failed to send voicemail SMS alert: %s", error)

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
            logger.warning(
                "Twilio denied access to recording for voicemail %d (HTTP %d). Check Twilio credentials in Settings.",
                voicemail_id,
                response.status_code,
            )
            raise TwilioAudioFetchError("Twilio denied access to the recording. Check Twilio credentials in Settings.", status_code=502)
        if response.status_code == 404:
            logger.warning(
                "Twilio returned 404 for voicemail %d recording — media may still be processing.",
                voicemail_id,
            )
            raise TwilioAudioFetchError("Recording is not ready yet. Try again in a few seconds.", status_code=503)
        if response.status_code >= 400:
            logger.warning(
                "Twilio returned unexpected HTTP %d for voicemail %d recording.",
                response.status_code,
                voicemail_id,
            )
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
        account_sid = TwilioService._clean_env("TWILIO_ACCOUNT_SID") or settings.get("account_sid")
        auth_token = TwilioService._clean_env("TWILIO_AUTH_TOKEN") or get_decrypted_twilio_auth_token()
        return account_sid, auth_token

    @staticmethod
    def _clean_env(name: str) -> str | None:
        value = os.getenv(name)
        if value is None:
            return None
        value = value.strip()
        return value or None
