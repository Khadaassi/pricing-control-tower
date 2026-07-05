from unittest.mock import MagicMock

from app.tools.price_tool import PriceTool


def make_price(**kwargs) -> dict:
    return {
        "id": 1,
        "product_id": 3,
        "product_code": "RUN-001",
        "product_name": "Running Shoes",
        "amount": "29.99",
        "currency_code": "EUR",
        "price_scope": "COUNTRY",
        "country_id": 1,
        "store_id": None,
        "status": "ACTIVE",
        **kwargs,
    }


class TestListPrices:
    def test_calls_correct_endpoint_without_filters(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_tool.list_prices()

        mock_backend_client.get.assert_called_once_with(
            path="/prices",
            user_email=None,
            params={},
        )

    def test_passes_product_id_filter_when_provided(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_tool.list_prices(product_id=3)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["product_id"] == 3

    def test_passes_store_id_filter_when_provided(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_tool.list_prices(store_id=2)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["store_id"] == 2

    def test_passes_country_id_filter_when_provided(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_tool.list_prices(country_id=1)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["country_id"] == 1

    def test_passes_user_email(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_tool.list_prices(user_email="user@example.com")

        mock_backend_client.get.assert_called_once_with(
            path="/prices",
            user_email="user@example.com",
            params={},
        )

    def test_returns_items_when_backend_returns_paginated_dict(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {
            "items": [make_price()],
            "total": 1,
        }

        result = price_tool.list_prices()

        assert result == [make_price()]

    def test_returns_list_when_backend_returns_a_list(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [make_price()]

        result = price_tool.list_prices()

        assert result == [make_price()]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = None

        result = price_tool.list_prices()

        assert result == []

    def test_omits_none_filters_from_params(
        self, price_tool: PriceTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_tool.list_prices(product_id=None, store_id=None, country_id=None)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params == {}
