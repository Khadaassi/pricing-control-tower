import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from services.api_client import ApiClientError


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard_user",
            password="Password123!",
            email="dashboard.user@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:dashboard")

    @patch("core.views.api_get")
    def test_dashboard_builds_kpi_cards_and_charts_from_api_data(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/stores":
                return []
            if endpoint == "/kpis":
                return {
                    "total_sales_count": 1000,
                    "promo_sales_count": 200,
                    "total_revenue": 50000.0,
                    "promo_revenue": 8000.0,
                    "promo_sales_share": 0.2,
                    "average_order_value": 50.0,
                    "total_quantity": 1500,
                }
            if endpoint == "/price-change-requests":
                return {"items": [{"status": "PENDING"}, {"status": "APPLIED"}], "total": 2}
            if endpoint == "/anomalies":
                return {
                    "items": [
                        {"severity": "HIGH", "is_resolved": False},
                        {"severity": "LOW", "is_resolved": True},
                    ],
                    "total": 2,
                }
            if endpoint == "/promotions":
                return {
                    "items": [
                        {"discount_type": "PERCENTAGE", "active": True},
                        {"discount_type": "FIXED_PRICE", "active": False},
                    ],
                    "total": 2,
                }
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["api_error"])

        kpi_cards = response.context["kpi_cards"]
        self.assertEqual(len(kpi_cards), 7)
        sales_card = next(c for c in kpi_cards if c["label"] == "Ventes totales")
        self.assertEqual(sales_card["value"], "1,000.00")

        sales_chart = json.loads(response.context["chart_sales_json"])
        self.assertEqual(sales_chart["series"], [200, 800])

        requests_chart = json.loads(response.context["chart_requests_json"])
        self.assertEqual(set(requests_chart["labels"]), {"PENDING", "APPLIED"})

        anomalies_severity = json.loads(response.context["chart_anomalies_severity_json"])
        self.assertEqual(set(anomalies_severity["labels"]), {"HIGH", "LOW"})

        anomalies_resolved = json.loads(response.context["chart_anomalies_resolved_json"])
        self.assertEqual(anomalies_resolved["series"], [1, 1])

        promos_status = json.loads(response.context["chart_promos_status_json"])
        self.assertEqual(promos_status["series"], [1, 1])

    @patch("core.views.api_get")
    def test_dashboard_sets_api_error_when_kpis_call_fails(self, mock_api_get):
        mock_api_get.side_effect = ApiClientError("Unable to connect to FastAPI backend.")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["api_error"],
            "Unable to connect to FastAPI backend.",
        )
        self.assertEqual(response.context["kpi_cards"], [])

    @patch("core.views.api_get")
    def test_dashboard_survives_secondary_endpoint_failures(self, mock_api_get):
        """The KPI cards must still render even if /anomalies or /promotions fail —
        those failures are swallowed (bare `except ApiClientError: pass`)."""

        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/kpis":
                return {
                    "total_sales_count": 10,
                    "promo_sales_count": 0,
                    "total_revenue": 100.0,
                    "promo_revenue": 0.0,
                    "promo_sales_share": 0.0,
                    "average_order_value": 10.0,
                    "total_quantity": 10,
                }
            raise ApiClientError("downstream failure")

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["api_error"])
        self.assertEqual(len(response.context["kpi_cards"]), 7)
        self.assertIsNone(response.context["chart_anomalies_severity_json"])
        self.assertIsNone(response.context["chart_promos_status_json"])
