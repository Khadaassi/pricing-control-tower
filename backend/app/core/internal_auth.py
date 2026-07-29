from __future__ import annotations

import jwt

from app.config import get_internal_auth_secret

ALGORITHM = "HS256"


class InvalidServiceToken(Exception):
    """Raised when an internal service token is missing, expired, or forged."""


def decode_service_token(token: str) -> str:
    try:
        payload = jwt.decode(token, get_internal_auth_secret(), algorithms=[ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise InvalidServiceToken(str(exc)) from exc

    email = payload.get("sub")

    if not isinstance(email, str) or not email:
        raise InvalidServiceToken("Token payload is missing the 'sub' claim")

    return email
