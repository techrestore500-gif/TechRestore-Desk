import logging
import smtplib

import pytest

from app.services.emailer import EmailDeliveryError, EmailService


class _FakeSMTPBase:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_called = False
        self.login_called_with = None
        self.sent_messages = []
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def ehlo(self):
        return None

    def starttls(self):
        self.starttls_called = True

    def login(self, username, password):
        self.login_called_with = (username, password)

    def send_message(self, message):
        self.sent_messages.append(message)


class _FakeSMTP(_FakeSMTPBase):
    instances = []


class _FakeSMTPSSL(_FakeSMTPBase):
    instances = []


def _set_base_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "techrestore500@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret-app-pass")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "techrestore500@gmail.com")
    monkeypatch.setenv("SMTP_FROM_NAME", "Tech Restore")


def test_smtp_starttls_mode(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("SMTP_USE_SSL", "false")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setenv("SMTP_TIMEOUT_SECONDS", "22")

    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", _FakeSMTPSSL)

    EmailService.send_invite_email(
        recipient_email="mattiskleinbh@gmail.com",
        recipient_name="Mattis",
        invite_link="https://desk.techrestoredesk.com/invite/token123",
        expires_in_hours=72,
    )

    assert len(_FakeSMTP.instances) == 1
    instance = _FakeSMTP.instances[-1]
    assert instance.host == "smtp.gmail.com"
    assert instance.port == 587
    assert instance.timeout == 22.0
    assert instance.starttls_called is True
    assert len(_FakeSMTPSSL.instances) == 0


def test_smtp_ssl_mode(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_STARTTLS", "false")

    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", _FakeSMTPSSL)

    EmailService.send_invite_email(
        recipient_email="mattiskleinbh@gmail.com",
        recipient_name="Mattis",
        invite_link="https://desk.techrestoredesk.com/invite/token123",
        expires_in_hours=72,
    )

    assert len(_FakeSMTPSSL.instances) == 1
    instance = _FakeSMTPSSL.instances[-1]
    assert instance.port == 465
    assert instance.starttls_called is False


def test_smtp_port_parse_error(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "abc")

    with pytest.raises(EmailDeliveryError) as error:
        EmailService.send_invite_email(
            recipient_email="mattiskleinbh@gmail.com",
            recipient_name="Mattis",
            invite_link="https://desk.techrestoredesk.com/invite/token123",
            expires_in_hours=72,
        )

    assert "SMTP_PORT is invalid" in str(error.value)


def test_smtp_logs_safe_diagnostics_without_secret(monkeypatch, caplog):
    _set_base_env(monkeypatch)

    class _BrokenSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self):
            raise OSError("Network unreachable")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(smtplib, "SMTP", _BrokenSMTP)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(EmailDeliveryError):
            EmailService.send_invite_email(
                recipient_email="mattiskleinbh@gmail.com",
                recipient_name="Mattis",
                invite_link="https://desk.techrestoredesk.com/invite/token123",
                expires_in_hours=72,
            )

    combined_logs = "\n".join(item.getMessage() for item in caplog.records)
    assert "SMTP connection failed" in combined_logs
    assert "secret-app-pass" not in combined_logs
    assert "techrestore500@gmail.com" not in combined_logs
