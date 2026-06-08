from __future__ import annotations

import logging
from dataclasses import dataclass

from twilio.rest import Client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmsSendResult:
    to_number: str
    from_number: str
    success: bool
    message_sid: str | None
    status: str | None
    error_message: str | None = None


def send_market_update_sms(
    *,
    twilio_account_sid: str,
    twilio_auth_token: str,
    from_number: str,
    to_number: str,
    message_body: str,
) -> SmsSendResult:
    result = send_market_update_sms_to_many(
        twilio_account_sid=twilio_account_sid,
        twilio_auth_token=twilio_auth_token,
        from_number=from_number,
        to_numbers=[to_number],
        message_body=message_body,
    )
    return result[0]


def send_market_update_sms_to_many(
    *,
    twilio_account_sid: str,
    twilio_auth_token: str,
    from_number: str,
    to_numbers: list[str],
    message_body: str,
) -> list[SmsSendResult]:
    client = Client(twilio_account_sid, twilio_auth_token)
    results: list[SmsSendResult] = []

    for to_number in to_numbers:
        try:
            response = client.messages.create(
                body=message_body,
                from_=from_number,
                to=to_number,
            )
            logger.info(
                "Market update SMS sent to=%s sid=%s status=%s",
                to_number,
                response.sid,
                response.status,
            )
            results.append(
                SmsSendResult(
                    to_number=to_number,
                    from_number=from_number,
                    success=True,
                    message_sid=response.sid,
                    status=response.status,
                )
            )
        except Exception as exc:
            logger.exception("Failed to send market update SMS to=%s", to_number)
            results.append(
                SmsSendResult(
                    to_number=to_number,
                    from_number=from_number,
                    success=False,
                    message_sid=None,
                    status=None,
                    error_message=str(exc),
                )
            )

    return results
