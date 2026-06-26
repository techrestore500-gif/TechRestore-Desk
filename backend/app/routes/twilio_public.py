from fastapi import APIRouter, Depends, Form, Query, Response
from xml.sax.saxutils import escape

from app.auth.twilio_signatures import verify_twilio_webhook_signature
from app.database import find_live_call_request_for_call_sid
from app.models import VoicemailRecordResponse
from app.services.twilio import TwilioService

router = APIRouter(prefix="/api", tags=["twilio-public"])


@router.post("/twilio/voice")
def post_twilio_voice(
    _: None = Depends(verify_twilio_webhook_signature),
    From: str | None = Form(default=None),
    To: str | None = Form(default=None),
    CallSid: str | None = Form(default=None),
) -> Response:
    TwilioService.remember_voice_call_context(CallSid, From, To)
    xml = TwilioService.build_voice_twiml(from_number=From, to_number=To)
    return Response(content=xml, media_type="application/xml")


@router.post("/twilio/voice/menu")
def post_twilio_voice_menu(
    _: None = Depends(verify_twilio_webhook_signature),
    Digits: str | None = Form(default=None),
    From: str | None = Form(default=None),
    To: str | None = Form(default=None),
    CallSid: str | None = Form(default=None),
) -> Response:
    TwilioService.remember_voice_call_context(CallSid, From, To)
    digits = (Digits or "").strip()
    if digits == "0":
        xml = TwilioService.build_voice_twiml(from_number=From, to_number=To)
    elif digits == "1":
        xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            "<Gather numDigits=\"1\" action=\"/api/twilio/voice/menu\" method=\"POST\" timeout=\"10\">"
            "<Say voice=\"Polly.Joanna\">Tech Restore is located at 500 West Kennedy Boulevard, in the back of the TAG office. "
            "A technician is usually in the shop from 6 to 8 PM. "
            "To return to the main menu, press 0.</Say>"
            "</Gather>"
            "<Redirect>/api/twilio/voice</Redirect>"
            "</Response>"
        )
    elif digits == "2":
        xml = TwilioService.build_voicemail_twiml(
            from_number=From,
            to_number=To,
            greeting_override=(
                "After the tone, please leave a clear, detailed message with your name, "
                "phone number, which device you have, and a description of the issue you are experiencing. "
                "We\u2019ll get back to you as soon as possible, usually within 24 hours."
            ),
        )
    elif digits == "3":
        xml = TwilioService.build_live_call_request_twiml(from_number=From, to_number=To, call_sid=CallSid)
    else:
        xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            "<Say voice=\"Polly.Joanna\">We did not receive a valid selection. Please leave a detailed message after the tone.</Say>"
            f"{TwilioService.build_voicemail_twiml(from_number=From, to_number=To, skip_response=True)}"
            "</Response>"
        )
    return Response(content=xml, media_type="application/xml")


@router.api_route("/twilio/live-accept", methods=["GET", "POST"])
def twilio_live_accept(
    _: None = Depends(verify_twilio_webhook_signature),
    call_sid: str | None = None,
) -> Response:
    request = None
    if call_sid:
        request = find_live_call_request_for_call_sid(call_sid)

    if request and request.get("admin_phone_number") and request.get("status") in {"pending", "accepted"}:
        settings = TwilioService.get_settings()
        caller_id = TwilioService._first_non_empty(
            settings.get("phone_number"),
            TwilioService._clean_env("TWILIO_PHONE_NUMBER"),
        )
        caller_id_attr = f' callerId="{escape(caller_id)}"' if caller_id else ""
        xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            f"<Say voice=\"Polly.Joanna\">The live technician is joining now. Please hold while we connect you.</Say>"
            f"<Dial{caller_id_attr}><Number>{escape(request['admin_phone_number'])}</Number></Dial>"
            "</Response>"
        )
    else:
        xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Response>"
            "<Say voice=\"Polly.Joanna\">No technician is available right now. Please leave a message after the tone. We will return your call as soon as possible.</Say>"
            f"{TwilioService.build_voicemail_twiml(from_number=None, to_number=None, skip_response=True)}"
            "</Response>"
        )

    return Response(content=xml, media_type="application/xml")


@router.post("/twilio/recording", response_model=VoicemailRecordResponse)
def post_twilio_recording(
    _: None = Depends(verify_twilio_webhook_signature),
    From: str | None = Form(default=None),
    To: str | None = Form(default=None),
    Caller: str | None = Form(default=None),
    Called: str | None = Form(default=None),
    AccountSid: str | None = Form(default=None),
    CallSid: str | None = Form(default=None),
    RecordingSid: str | None = Form(default=None),
    RecordingUrl: str | None = Form(default=None),
    RecordingDuration: str | None = Form(default=None),
    TranscriptionText: str | None = Form(default=None),
) -> VoicemailRecordResponse:
    record = TwilioService.record_voice_callback(
        {
            "From": From,
            "To": To,
            "Caller": Caller,
            "Called": Called,
            "AccountSid": AccountSid,
            "CallSid": CallSid,
            "RecordingSid": RecordingSid,
            "RecordingUrl": RecordingUrl,
            "RecordingDuration": RecordingDuration,
            "TranscriptionText": TranscriptionText,
        }
    )
    return VoicemailRecordResponse.model_validate(record)


@router.api_route("/twilio/outbound-call", methods=["GET", "POST"])
def twilio_outbound_call_prompt(
    _: None = Depends(verify_twilio_webhook_signature),
    to_number: str | None = Query(default=None),
    contact_name: str | None = Query(default=None),
    voicemail_id: int | None = Query(default=None),
) -> Response:
    xml = TwilioService.build_outbound_call_twiml(
        to_number=to_number,
        contact_name=contact_name,
        voicemail_id=voicemail_id,
    )
    return Response(content=xml, media_type="application/xml")
