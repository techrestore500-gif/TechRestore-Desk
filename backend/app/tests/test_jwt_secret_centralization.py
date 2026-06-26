from types import SimpleNamespace

import jwt as pyjwt
import pytest

from app.core.settings import get_settings
from app.utils import jwt as jwt_utils


STRONG_JWT_SECRET = "jwt-secret-stage1-validation-minimum-length-32+"
STRONG_SECRET_KEY = "legacy-secret-key-stage1-validation-minimum-32+"
STRONG_JWT_SECRET_2 = "jwt-secret-stage1-rotated-value-minimum-length-32+"


def test_jwt_secret_configuration_is_used(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", STRONG_JWT_SECRET)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)

    token, _ = jwt_utils.create_access_token(subject="owner", role="owner", user_id=1)
    payload = jwt_utils.decode_access_token(token)
    assert payload["sub"] == "owner"
    assert payload["uid"] == 1


def test_legacy_secret_key_compatibility_when_jwt_secret_missing(monkeypatch):
    monkeypatch.delenv("TECH_RESTORE_JWT_SECRET", raising=False)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)

    settings = get_settings()
    assert settings.jwt_secret == STRONG_SECRET_KEY

    token, _ = jwt_utils.create_access_token(subject="admin", role="admin", user_id=9)
    payload = jwt_utils.decode_access_token(token)
    assert payload["uid"] == 9


def test_jwt_secret_precedence_prefers_dedicated_setting(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", STRONG_JWT_SECRET)
    monkeypatch.setenv("SECRET_KEY", STRONG_SECRET_KEY)

    settings = get_settings()
    assert settings.jwt_secret == STRONG_JWT_SECRET


def test_production_missing_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.delenv("TECH_RESTORE_JWT_SECRET", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValueError, match="TECH_RESTORE_JWT_SECRET must be set"):
        get_settings()


def test_production_known_default_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", "dev-insecure-secret-change-me")

    with pytest.raises(ValueError, match="TECH_RESTORE_JWT_SECRET must be set"):
        get_settings()


@pytest.mark.parametrize(
    "secret",
    [
        "changeme",
        "placeholder",
        "short-secret-123",
    ],
)
def test_production_placeholder_or_weak_secret_is_rejected(monkeypatch, secret):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "production")
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", secret)

    with pytest.raises(ValueError):
        get_settings()


def test_development_default_secret_is_allowed(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "development")
    monkeypatch.delenv("TECH_RESTORE_JWT_SECRET", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = get_settings()
    assert settings.jwt_secret == "dev-insecure-secret-change-me"


def test_token_rejected_after_secret_rotation(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", STRONG_JWT_SECRET)
    token, _ = jwt_utils.create_access_token(subject="rotating-user", role="admin", user_id=7)

    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", STRONG_JWT_SECRET_2)
    with pytest.raises(pyjwt.InvalidTokenError):
        jwt_utils.decode_access_token(token)


def test_jwt_utility_does_not_bypass_settings(monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_JWT_SECRET", STRONG_JWT_SECRET)

    forced_secret = "forced-secret-from-settings-call-minimum-length+"
    monkeypatch.setattr(jwt_utils, "get_settings", lambda: SimpleNamespace(jwt_secret=forced_secret))

    token, _ = jwt_utils.create_access_token(subject="settings-user", role="manager", user_id=33)
    payload = pyjwt.decode(token, forced_secret, algorithms=[jwt_utils.JWT_ALGORITHM])
    assert payload["sub"] == "settings-user"
