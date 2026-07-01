from typing import Any

from app.clients.backend_client import BackendClient


class PriceTool:

    def __init__(self, backend_client: BackendClient | None = None) -> None:
        self.backend_client = backend_client or BackendClient()

    def list_prices(
        self,
        product_id: int | None = None,
        store_id: int | None = None,
        country_id: int | None = None,
        user_email: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if product_id is not None:
            params["product_id"] = product_id
        if store_id is not None:
            params["store_id"] = store_id
        if country_id is not None:
            params["country_id"] = country_id

        result = self.backend_client.get(
            path="/prices",
            user_email=user_email,
            params=params,
        )
        return self._normalize(result)

    def _normalize(self, result: Any) -> list[dict[str, Any]]:
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "items" in result:
            return result["items"]
        return []
