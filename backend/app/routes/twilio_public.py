from fastapi import APIRouter, Form, Response

from app.models import VoicemailRecordResponse
from app.services.twilio import TwilioService

router = APIRouter(prefix="/api", tags=["twilio-public"])


@router.post("/twilio/voice")
def post_twilio_voice(
    From: str | None = Form(default=None),
    To: str | None = Form(default=None),
    CallSid: str | None = Form(default=None),
) -> Response:
    TwilioService.remember_voice_call_context(CallSid, From, To)
    xml = TwilioService.build_voice_twiml(from_number=From, to_number=To)
    return Response(content=xml, media_type="application/xml")


@router.post("/twilio/recording", response_model=VoicemailRecordResponse)
def post_twilio_recording(
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
