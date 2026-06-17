from __future__ import annotations

from fastapi import APIRouter, Form, Response
from xml.sax.saxutils import escape

from app.services.twilio import TwilioService
from market_updates.keyword_handlers import handle_inbound_market_sms

router = APIRouter(prefix="/api", tags=["market-updates-public"])


@router.post("/market-updates/sms")
def post_market_updates_sms(
    From: str | None = Form(default=None),
    Body: str | None = Form(default=None),
    MessageSid: str | None = Form(default=None),
) -> Response:
    from_number = (From or "").strip()
    body = Body or ""
    _ = MessageSid

    message = TwilioService.handle_admin_live_sms_reply(from_number=from_number, message_body=body)
    if message is None:
        message = handle_inbound_market_sms(from_number=from_number, body=body)

    xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response>"
        f"<Message>{escape(message)}</Message>"
        "</Response>"
    )
    return Response(content=xml, media_type="application/xml")
