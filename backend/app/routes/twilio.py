from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth.dependencies import require_role
from app.models import (
    TwilioOutboundCallRequest,
    TwilioOutboundCallResponse,
    TwilioSettingsResponse,
    TwilioSettingsUpdate,
    TwilioSetupStatusResponse,
    VoicemailRecordResponse,
    VoicemailRecordUpdate,
)
from app.services.twilio import TwilioAudioFetchError, TwilioService

router = APIRouter(prefix="/api", tags=["twilio"])


@router.get("/settings/twilio", response_model=TwilioSettingsResponse)
def get_twilio_settings(_: dict = Depends(require_role("admin"))) -> TwilioSettingsResponse:
    return TwilioSettingsResponse.model_validate(TwilioService.get_settings())


@router.put("/settings/twilio", response_model=TwilioSettingsResponse)
def put_twilio_settings(payload: TwilioSettingsUpdate, _: dict = Depends(require_role("admin"))) -> TwilioSettingsResponse:
    return TwilioSettingsResponse.model_validate(TwilioService.update_settings(payload.model_dump(exclude_unset=True)))


@router.delete("/settings/twilio", response_model=TwilioSettingsResponse)
def delete_twilio_settings(_: dict = Depends(require_role("admin"))) -> TwilioSettingsResponse:
    return TwilioSettingsResponse.model_validate(TwilioService.clear_settings())


@router.post("/twilio/outbound-calls", response_model=TwilioOutboundCallResponse)
def post_twilio_outbound_call(
    payload: TwilioOutboundCallRequest,
    _: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> TwilioOutboundCallResponse:
    try:
        record = TwilioService.place_outbound_call(payload.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return TwilioOutboundCallResponse.model_validate(record)


@router.get("/settings/twilio/setup-status", response_model=TwilioSetupStatusResponse)
def get_twilio_setup_status(_: dict = Depends(require_role("admin"))) -> TwilioSetupStatusResponse:
    return TwilioSetupStatusResponse.model_validate(TwilioService.get_setup_status())


@router.get("/voicemails", response_model=list[VoicemailRecordResponse])
def get_voicemail_inbox(_: dict = Depends(require_role("admin", "front_desk", "technician"))) -> list[VoicemailRecordResponse]:
    return [VoicemailRecordResponse.model_validate(item) for item in TwilioService.list_voicemails()]


@router.patch("/voicemails/{voicemail_id}", response_model=VoicemailRecordResponse)
def patch_voicemail(
    voicemail_id: int,
    payload: VoicemailRecordUpdate,
    _: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> VoicemailRecordResponse:
    record = TwilioService.update_voicemail(voicemail_id, payload.model_dump(exclude_unset=True))
    if record is None:
        raise HTTPException(status_code=404, detail="Voicemail not found")
    return VoicemailRecordResponse.model_validate(record)


@router.delete("/voicemails/{voicemail_id}")
def delete_voicemail(
    voicemail_id: int,
    _: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> dict:
    deleted = TwilioService.delete_voicemail(voicemail_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Voicemail not found")
    return {"deleted": True}


@router.get("/voicemails/{voicemail_id}/audio")
def get_voicemail_audio(voicemail_id: int, _: dict = Depends(require_role("admin", "front_desk", "technician"))) -> Response:
    try:
        payload = TwilioService.fetch_recording_audio(voicemail_id)
    except TwilioAudioFetchError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
    if payload is None:
        raise HTTPException(status_code=404, detail="Voicemail audio not available")
    content, content_type = payload
    return Response(content=content, media_type=content_type)
