from typing import Any

from app.clients.backend_client import BackendClient


class ReferenceDataTool:

    def __init__(self, backend_client: BackendClient | None = None) -> None:
        self.backend_client = backend_client or BackendClient()

    def list_countries(self, user_email: str | None = None) -> list[dict[str, Any]]:
        result = self.backend_client.get(
            path="/countries",
            user_email=user_email,
        )
        return self._normalize(result)

    def list_stores(
        self,
        country_id: int | None = None,
        user_email: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if country_id is not None:
            params["country_id"] = country_id

        result = self.backend_client.get(
            path="/stores",
            user_email=user_email,
            params=params,
        )
        return self._normalize(result)

    def list_product_families(self, user_email: str | None = None) -> list[dict[str, Any]]:
        result = self.backend_client.get(
            path="/product-families",
            user_email=user_email,
        )
        return self._normalize(result)

    def list_products(
        self,
        family_id: int | None = None,
        active: bool | None = None,
        user_email: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if family_id is not None:
            params["product_family_id"] = family_id
        if active is not None:
            params["active"] = active

        result = self.backend_client.get(
            path="/products",
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
