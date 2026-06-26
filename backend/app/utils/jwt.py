from datetime import UTC, datetime, timedelta

import jwt

from app.core.settings import get_settings


JWT_ALGORITHM = "HS256"
DEFAULT_EXP_MINUTES = 60


def _jwt_secret() -> str:
    return get_settings().jwt_secret


def create_access_token(subject: str, role: str, user_id: int, expires_minutes: int = DEFAULT_EXP_MINUTES) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "uid": user_id,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
