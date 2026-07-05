from unittest.mock import MagicMock

from app.tools.promotion_tool import PromotionTool


def make_promotion(active: bool = True, **extra) -> dict:
    return {
        "id": 1,
        "product_id": 5,
        "discount_type": "PERCENTAGE",
        "discount_value": "20.00",
        "start_date": "2026-06-01",
        "end_date": "2026-06-15",
        "active": active,
        **extra,
    }


class TestListPromotions:
    def test_calls_correct_endpoint_without_filters(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        promotion_tool.list_promotions()

        mock_backend_client.get.assert_called_once_with(
            path="/promotions",
            user_email=None,
            params={},
        )

    def test_passes_active_filter_when_provided(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        promotion_tool.list_promotions(active=True)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["active"] is True

    def test_passes_store_id_filter_when_provided(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        promotion_tool.list_promotions(store_id=3)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["store_id"] == 3

    def test_passes_country_id_and_product_id_filters(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        promotion_tool.list_promotions(country_id=1, product_id=7)

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params["country_id"] == 1
        assert called_params["product_id"] == 7

    def test_passes_user_email(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        promotion_tool.list_promotions(user_email="user@example.com")

        mock_backend_client.get.assert_called_once_with(
            path="/promotions",
            user_email="user@example.com",
            params={},
        )

    def test_returns_items_when_backend_returns_paginated_dict(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {
            "items": [make_promotion(active=True)],
            "total": 1,
        }

        result = promotion_tool.list_promotions()

        assert result == [make_promotion(active=True)]

    def test_returns_list_when_backend_returns_a_list(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [make_promotion(active=False)]

        result = promotion_tool.list_promotions()

        assert result == [make_promotion(active=False)]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = 42

        result = promotion_tool.list_promotions()

        assert result == []

    def test_omits_none_filters_from_params(
        self, promotion_tool: PromotionTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"items": [], "total": 0}

        promotion_tool.list_promotions(
            active=None, store_id=None, country_id=None, product_id=None
        )

        called_params = mock_backend_client.get.call_args.kwargs["params"]
        assert called_params == {}
