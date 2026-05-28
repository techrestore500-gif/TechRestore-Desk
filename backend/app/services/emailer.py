from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from html import escape


logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    pass


class EmailService:
    @staticmethod
    def _to_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

    @staticmethod
    def _smtp_host() -> str:
        return os.getenv("SMTP_HOST", "").strip()

    @staticmethod
    def _smtp_port() -> int:
        raw = os.getenv("SMTP_PORT", "587").strip()
        try:
            return int(raw)
        except ValueError as error:
            raise EmailDeliveryError("SMTP_PORT is invalid") from error

    @staticmethod
    def _smtp_timeout_seconds() -> float:
        raw = os.getenv("SMTP_TIMEOUT_SECONDS", "20").strip()
        try:
            return max(3.0, float(raw))
        except ValueError as error:
            raise EmailDeliveryError("SMTP_TIMEOUT_SECONDS is invalid") from error

    @staticmethod
    def _use_ssl() -> bool:
        return EmailService._to_bool("SMTP_USE_SSL", False)

    @staticmethod
    def _starttls_enabled() -> bool:
        return EmailService._to_bool("SMTP_STARTTLS", True)

    @staticmethod
    def _smtp_username() -> str:
        return os.getenv("SMTP_USERNAME", "").strip()

    @staticmethod
    def _smtp_password() -> str:
        return os.getenv("SMTP_PASSWORD", "").strip()

    @staticmethod
    def _from_email() -> str:
        return os.getenv("SMTP_FROM_EMAIL", "").strip()

    @staticmethod
    def _from_name() -> str:
        return os.getenv("SMTP_FROM_NAME", "Tech Restore").strip() or "Tech Restore"

    @staticmethod
    def _validate_config() -> None:
        required = {
            "SMTP_HOST": EmailService._smtp_host(),
            "SMTP_USERNAME": EmailService._smtp_username(),
            "SMTP_PASSWORD": EmailService._smtp_password(),
            "SMTP_FROM_EMAIL": EmailService._from_email(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise EmailDeliveryError(f"Email is not configured ({', '.join(missing)})")

    @staticmethod
    def send_invite_email(*, recipient_email: str, recipient_name: str | None, invite_link: str, expires_in_hours: int) -> None:
        EmailService._validate_config()
        to_email = recipient_email.strip().lower()
        greeting_name = (recipient_name or "there").strip() or "there"

        subject = "Set up your Tech Restore Desk account"
        html_body = f"""
<!DOCTYPE html>
<html>
  <body style=\"font-family: Arial, sans-serif; color: #16322c; margin: 0; padding: 0; background: #f5efe3;\">
    <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"padding: 28px 12px;\">
      <tr>
        <td align=\"center\">
          <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width: 560px; background: #ffffff; border: 1px solid #d7c8ac; border-radius: 12px;\">
            <tr>
              <td style=\"padding: 24px;\">
                <h2 style=\"margin: 0 0 14px; color: #16322c;\">Tech Restore Desk</h2>
                <p style=\"margin: 0 0 10px;\">Hi {escape(greeting_name)},</p>
                <p style=\"margin: 0 0 10px;\">You've been invited to set up the owner account for Tech Restore Desk.</p>
                <p style=\"margin: 0 0 18px;\">Click the button below to create your account.</p>
                <p style=\"margin: 0 0 20px;\">
                  <a href=\"{escape(invite_link)}\" style=\"display: inline-block; background: #1d6557; color: #f7f2e8; text-decoration: none; font-weight: 700; padding: 11px 16px; border-radius: 8px;\">Create Tech Restore Account</a>
                </p>
                <p style=\"margin: 0 0 10px;\">This link can only be used once and will expire in {expires_in_hours} hours.</p>
                <p style=\"margin: 0 0 12px;\">If you did not expect this email, you can ignore it.</p>
                <p style=\"margin: 0; font-size: 13px; color: #365a52;\">Direct link: <a href=\"{escape(invite_link)}\">{escape(invite_link)}</a></p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()

        text_body = (
            f"Hi {greeting_name},\n\n"
            "You've been invited to set up the owner account for Tech Restore Desk.\n"
            f"Create your account: {invite_link}\n\n"
            f"This link can only be used once and expires in {expires_in_hours} hours.\n"
            "If you did not expect this email, you can ignore it.\n"
        )

        message = EmailMessage()
        from_name = EmailService._from_name()
        from_email = EmailService._from_email()
        message["Subject"] = subject
        message["From"] = f"{from_name} <{from_email}>"
        message["To"] = to_email
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        smtp_host = EmailService._smtp_host()
        smtp_port = EmailService._smtp_port()
        smtp_timeout = EmailService._smtp_timeout_seconds()
        use_ssl = EmailService._use_ssl()
        use_starttls = EmailService._starttls_enabled() and not use_ssl
        smtp_username = EmailService._smtp_username()
        smtp_password = EmailService._smtp_password()

        smtp_factory = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        try:
            with smtp_factory(smtp_host, smtp_port, timeout=smtp_timeout) as smtp:
                smtp.ehlo()
                if use_starttls:
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
        except smtplib.SMTPException as error:
            logger.warning(
                "SMTP send failed (%s): %s [host=%s port=%s ssl=%s starttls=%s timeout=%ss]",
                error.__class__.__name__,
                str(error),
                smtp_host,
                smtp_port,
                use_ssl,
                use_starttls,
                smtp_timeout,
            )
            raise EmailDeliveryError("Failed to deliver invite email") from error
        except OSError as error:
            logger.warning(
                "SMTP connection failed (%s): %s [host=%s port=%s ssl=%s starttls=%s timeout=%ss]",
                error.__class__.__name__,
                str(error),
                smtp_host,
                smtp_port,
                use_ssl,
                use_starttls,
                smtp_timeout,
            )
            raise EmailDeliveryError("Could not connect to SMTP server") from error
