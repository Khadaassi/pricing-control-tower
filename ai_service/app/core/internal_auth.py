from __future__ import annotations

import time

import jwt

from app.core.config import settings

ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60


def issue_service_token(user_email: str) -> str:
    now = int(time.time())

    payload = {
        "sub": user_email,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }

    return jwt.encode(payload, settings.internal_auth_secret, algorithm=ALGORITHM)


class InvalidServiceToken(Exception):
    """Raised when an internal service token is missing, expired, or forged."""


def decode_service_token(token: str) -> str:
    """Mirrors backend/app/core/internal_auth.py::decode_service_token — same
    shared secret, same claim shape, used here to authenticate the inbound
    Django -> ai_service call rather than an outbound one."""
    try:
        payload = jwt.decode(token, settings.internal_auth_secret, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise InvalidServiceToken(str(exc)) from exc

    caller = payload.get("sub")

    if not isinstance(caller, str) or not caller:
        raise InvalidServiceToken("Token payload is missing the 'sub' claim")

    return caller
