from unittest.mock import MagicMock

from app.tools.price_change_request_tool import PriceChangeRequestTool


def make_request(status: str = "PENDING", **extra) -> dict:
    return {"id": 1, "product_id": 4, "status": status, "requested_price_amount": "19.99", **extra}


class TestListPriceChangeRequests:
    def test_calls_correct_endpoint(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_change_request_tool.list_price_change_requests()

        mock_backend_client.get.assert_called_once_with(
            path="/price-change-requests",
            user_email=None,
            params={},
        )

    def test_passes_status_filter_when_provided(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_change_request_tool.list_price_change_requests(status="PENDING")

        mock_backend_client.get.assert_called_once_with(
            path="/price-change-requests",
            user_email=None,
            params={"status": "PENDING"},
        )

    def test_passes_product_id_filter_when_provided(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_change_request_tool.list_price_change_requests(product_id=5)

        mock_backend_client.get.assert_called_once_with(
            path="/price-change-requests",
            user_email=None,
            params={"product_id": 5},
        )

    def test_passes_store_and_country_id_filters(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_change_request_tool.list_price_change_requests(store_id=2, country_id=1)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["store_id"] == 2
        assert called_params["country_id"] == 1

    def test_passes_user_email(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_change_request_tool.list_price_change_requests(user_email="user@example.com")

        mock_backend_client.get.assert_called_once_with(
            path="/price-change-requests",
            user_email="user@example.com",
            params={},
        )

    def test_returns_items_when_backend_returns_paginated_dict(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {
            "items": [make_request("PENDING")],
            "total": 1,
        }

        result = price_change_request_tool.list_price_change_requests()

        assert result == [make_request("PENDING")]

    def test_returns_list_when_backend_returns_a_list(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [make_request("APPROVED")]

        result = price_change_request_tool.list_price_change_requests()

        assert result == [make_request("APPROVED")]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = "unexpected"

        result = price_change_request_tool.list_price_change_requests()

        assert result == []

    def test_omits_none_filters_from_params(
        self, price_change_request_tool: PriceChangeRequestTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        price_change_request_tool.list_price_change_requests(
            status=None, product_id=None, store_id=None, country_id=None
        )

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params == {}
