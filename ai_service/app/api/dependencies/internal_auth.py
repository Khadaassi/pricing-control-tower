from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.internal_auth import InvalidServiceToken, decode_service_token

_bearer_scheme = HTTPBearer(auto_error=False)


def require_service_caller(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Authenticates the caller of POST /chat (Django frontend), mirroring
    backend/app/api/dependencies/current_user.py::get_current_business_user.

    Returns the token's 'sub' claim — the identity of the calling service, not
    the business end-user (that's request.user_email, unrelated to this
    token and used separately for RBAC by the backend)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        return decode_service_token(credentials.credentials)
    except InvalidServiceToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired service token",
        ) from exc
