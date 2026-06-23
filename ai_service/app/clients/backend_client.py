from typing import Any

import httpx

from app.core.config import settings


class BackendClient:
    def __init__(self) -> None:
        self.base_url = settings.backend_api_url.rstrip("/")

    def get(
        self,
        path: str,
        user_email: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        headers = {
            "X-User-Email": user_email,
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                url,
                headers=headers,
                params=params,
            )

        response.raise_for_status()
        return response.json()