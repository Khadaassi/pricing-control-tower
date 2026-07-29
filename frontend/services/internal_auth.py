from __future__ import annotations

import time

import jwt
from django.conf import settings

ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 60


def issue_service_token(user_email: str) -> str:
    now = int(time.time())

    payload = {
        "sub": user_email,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }

    return jwt.encode(payload, settings.INTERNAL_AUTH_SECRET, algorithm=ALGORITHM)
