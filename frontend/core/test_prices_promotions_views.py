from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from services.api_client import ApiClientError


class PricesViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="prices_user",
            password="Password123!",
            email="prices.user@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:prices")

    @patch("core.views.api_get")
    def test_prices_view_renders_paginated_list(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/prices":
                return {
                    "items": [
                        {
                            "product_id": 1,
                            "product_code": "P1",
                            "product_name": "Product One",
                            "price_scope": "COUNTRY",
                            "price_type": "STANDARD",
                            "amount": "19.99",
                            "currency_code": "EUR",
                            "country_id": 1,
                            "store_id": None,
                            "effective_from": "2026-01-01",
                            "effective_to": None,
                            "status": "ACTIVE",
                            "promotion_id": None,
                        }
                    ],
                    "total": 1,
                }
            if endpoint in ("/products", "/countries", "/stores"):
                return []
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["api_error"])

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)

        row = list(page_obj)[0]
        self.assertEqual(row["product_code"], "P1")
        self.assertEqual(row["scope_label"], "Prix pays")
        self.assertEqual(row["amount"], "19.99 EUR")

    @patch("core.views.api_get")
    def test_prices_view_sets_api_error_on_failure(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/prices":
                raise ApiClientError("FastAPI backend returned an error: 500")
            return []

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["api_error"],
            "FastAPI backend returned an error: 500",
        )
        self.assertEqual(response.context["prices"], [])


class PromotionsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="promotions_user",
            password="Password123!",
            email="promotions.user@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:promotions")

    @patch("core.views.api_get")
    def test_promotions_view_renders_paginated_list(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/promotions":
                return {
                    "items": [
                        {
                            "id": 1,
                            "code": "PROMO-1",
                            "name": "Promo One",
                            "description": "x",
                            "discount_type": "PERCENTAGE",
                            "discount_value": "10.00",
                            "product_id": 1,
                            "country_id": 1,
                            "store_id": None,
                            "start_date": "2026-01-01",
                            "end_date": "2026-01-31",
                            "active": True,
                        }
                    ],
                    "total": 1,
                }
            if endpoint in ("/products", "/countries", "/stores"):
                return []
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["api_error"])

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)

        row = list(page_obj)[0]
        self.assertEqual(row["code"], "PROMO-1")
        self.assertEqual(row["discount_value"], "10.00%")
        self.assertEqual(row["scope"], "Promotion pays")
        self.assertEqual(row["status"], "Active")

    @patch("core.views.api_get")
    def test_promotions_view_sets_api_error_on_failure(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/promotions":
                raise ApiClientError("Unable to connect to FastAPI backend.")
            return []

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["api_error"],
            "Unable to connect to FastAPI backend.",
        )
        self.assertEqual(response.context["promotions"], [])
