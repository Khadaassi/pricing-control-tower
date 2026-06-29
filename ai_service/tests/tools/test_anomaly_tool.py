from unittest.mock import MagicMock

from app.tools.anomaly_tool import AnomalyTool


def make_anomaly(anomaly_type: str, **extra) -> dict:
    return {"anomaly_type": anomaly_type, **extra}


class TestListAnomalies:
    def test_returns_list_when_backend_returns_a_list(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [make_anomaly("UNDERPERFORMING_PROMO")]

        result = anomaly_tool.list_anomalies(user_email="user@example.com")

        assert result == [make_anomaly("UNDERPERFORMING_PROMO")]

    def test_returns_items_when_backend_returns_a_paginated_dict(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {
            "items": [make_anomaly("INEFFECTIVE_DISCOUNT")],
            "total": 1,
        }

        result = anomaly_tool.list_anomalies(user_email="user@example.com")

        assert result == [make_anomaly("INEFFECTIVE_DISCOUNT")]

    def test_returns_empty_list_for_unexpected_backend_response(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = {"unexpected": "shape"}

        result = anomaly_tool.list_anomalies(user_email="user@example.com")

        assert result == []

    def test_passes_user_email_and_default_pagination(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        anomaly_tool.list_anomalies(user_email="user@example.com")

        mock_backend_client.get.assert_called_once_with(
            path="/anomalies",
            user_email="user@example.com",
            params={"limit": 20, "offset": 0},
        )

    def test_includes_only_provided_optional_filters(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        anomaly_tool.list_anomalies(user_email="user@example.com", store_id=42)

        mock_backend_client.get.assert_called_once_with(
            path="/anomalies",
            user_email="user@example.com",
            params={"limit": 20, "offset": 0, "store_id": 42},
        )


class TestExplainAnomaly:
    def test_explains_known_anomaly_type(self, anomaly_tool: AnomalyTool) -> None:
        anomaly = make_anomaly("UNDERPERFORMING_PROMO")

        result = anomaly_tool.explain_anomaly(anomaly)

        assert result["anomaly"] == anomaly
        assert result["explanation"]["label"] == "Underperforming promotion"

    def test_falls_back_to_type_key_when_anomaly_type_missing(
        self, anomaly_tool: AnomalyTool
    ) -> None:
        anomaly = {"type": "PRICE_ABOVE_REFERENCE"}

        result = anomaly_tool.explain_anomaly(anomaly)

        assert result["explanation"]["label"] == "Store price above country reference"

    def test_unknown_anomaly_type_returns_generic_explanation(
        self, anomaly_tool: AnomalyTool
    ) -> None:
        anomaly = make_anomaly("SOME_NEW_ANOMALY")

        result = anomaly_tool.explain_anomaly(anomaly)

        assert result["explanation"]["label"] == "Unknown anomaly"


class TestExplainAnomalies:
    def test_explains_every_anomaly_in_the_list(self, anomaly_tool: AnomalyTool) -> None:
        anomalies = [
            make_anomaly("UNDERPERFORMING_PROMO"),
            make_anomaly("INEFFECTIVE_DISCOUNT"),
        ]

        result = anomaly_tool.explain_anomalies(anomalies)

        assert len(result) == 2
        assert result[0]["explanation"]["label"] == "Underperforming promotion"
        assert result[1]["explanation"]["label"] == "Ineffective discount"

    def test_empty_list_returns_empty_list(self, anomaly_tool: AnomalyTool) -> None:
        assert anomaly_tool.explain_anomalies([]) == []


class TestListStoreCountryPriceMismatches:
    def test_filters_and_explains_only_price_above_reference_anomalies(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [
            make_anomaly("PRICE_ABOVE_REFERENCE", id=1),
            make_anomaly("UNDERPERFORMING_PROMO", id=2),
            make_anomaly("PRICE_ABOVE_REFERENCE", id=3),
        ]

        result = anomaly_tool.list_store_country_price_mismatches(
            user_email="user@example.com",
            store_id=42,
        )

        assert [entry["anomaly"]["id"] for entry in result] == [1, 3]
        assert all(
            entry["explanation"]["label"] == "Store price above country reference"
            for entry in result
        )

    def test_requests_anomalies_scoped_to_store(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = []

        anomaly_tool.list_store_country_price_mismatches(
            user_email="user@example.com",
            store_id=42,
        )

        mock_backend_client.get.assert_called_once_with(
            path="/anomalies",
            user_email="user@example.com",
            params={"limit": 20, "offset": 0, "store_id": 42},
        )

    def test_returns_empty_list_when_no_mismatches_found(
        self, anomaly_tool: AnomalyTool, mock_backend_client: MagicMock
    ) -> None:
        mock_backend_client.get.return_value = [make_anomaly("UNDERPERFORMING_PROMO")]

        result = anomaly_tool.list_store_country_price_mismatches(
            user_email="user@example.com",
            store_id=42,
        )

        assert result == []
