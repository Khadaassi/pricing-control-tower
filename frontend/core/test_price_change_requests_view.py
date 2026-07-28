from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from services.api_client import ApiClientError, ApiResponseError


class PriceChangeRequestsViewGetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pcr_view_user",
            password="Password123!",
            email="pcr.view.user@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:price_change_requests")

    @patch("core.views.price_change_requests.api_get")
    def test_renders_paginated_list(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/price-change-requests":
                return {
                    "items": [
                        {
                            "id": 42,
                            "product_id": 1,
                            "country_id": 1,
                            "store_id": None,
                            "old_price_amount": "10.00",
                            "requested_price_amount": "12.00",
                            "status": "PENDING",
                            "justification": "x",
                            "requested_effective_date": "2026-07-01",
                            "rejection_reason": None,
                            "created_at": "2026-06-01T00:00:00Z",
                        }
                    ],
                    "total": 1,
                }
            if endpoint in ("/products", "/countries"):
                return []
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["api_error"])

        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 1)

        row = list(page_obj)[0]
        self.assertEqual(row["id"], 42)
        self.assertEqual(row["scope"], "Demande pays")
        self.assertEqual(row["price_delta_pct"], 20.0)

    @patch("core.views.price_change_requests.api_get")
    def test_sets_api_error_on_failure(self, mock_api_get):
        def fake_api_get(endpoint, params=None, user_email=None):
            if endpoint == "/price-change-requests":
                raise ApiClientError("Unable to connect to FastAPI backend.")
            return []

        mock_api_get.side_effect = fake_api_get

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["api_error"],
            "Unable to connect to FastAPI backend.",
        )


class PriceChangeRequestsWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pcr_workflow_user",
            password="Password123!",
            email="pcr.workflow.user@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:price_change_requests")

    @patch("core.views.price_change_requests.api_post")
    def test_approve_action_posts_to_backend_and_redirects_with_success(self, mock_api_post):
        mock_api_post.return_value = {"id": 42, "status": "APPLIED"}

        response = self.client.post(
            self.url,
            {"action": "approve", "request_id": "42"},
        )

        self.assertRedirects(response, self.url)
        mock_api_post.assert_called_once_with(
            "/price-change-requests/42/approve",
            payload=None,
            user_email="pcr.workflow.user@pct.local",
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("approuvée", str(messages[0]))

    @patch("core.views.price_change_requests.api_post")
    def test_approve_action_shows_error_message_on_api_failure(self, mock_api_post):
        mock_api_post.side_effect = ApiResponseError("Permission denied: APPROVE_PRICE_REQUEST is required")

        response = self.client.post(
            self.url,
            {"action": "approve", "request_id": "42"},
        )

        self.assertRedirects(response, self.url)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("n’a pas pu être approuvée", str(messages[0]))
        self.assertIn("Permission denied", str(messages[0]))

    @patch("core.views.price_change_requests.api_post")
    def test_reject_action_posts_reason_and_redirects_with_success(self, mock_api_post):
        mock_api_post.return_value = {"id": 42, "status": "REJECTED"}

        response = self.client.post(
            self.url,
            {"action": "reject", "request_id": "42", "reason": "Prix trop élevé"},
        )

        self.assertRedirects(response, self.url)
        mock_api_post.assert_called_once_with(
            "/price-change-requests/42/reject",
            payload={"reason": "Prix trop élevé"},
            user_email="pcr.workflow.user@pct.local",
        )

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("refusée", str(messages[0]))

    def test_reject_action_without_reason_does_not_call_backend(self):
        with patch("core.views.price_change_requests.api_post") as mock_api_post:
            response = self.client.post(
                self.url,
                {"action": "reject", "request_id": "42", "reason": "   "},
            )

            mock_api_post.assert_not_called()

        self.assertRedirects(response, self.url)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("motif de refus est requis", str(messages[0]))

    def test_post_without_request_id_shows_error(self):
        response = self.client.post(self.url, {"action": "approve"})

        self.assertRedirects(response, self.url)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Identifiant", str(messages[0]))

    def test_post_with_unknown_action_shows_error(self):
        response = self.client.post(
            self.url,
            {"action": "cancel", "request_id": "42"},
        )

        self.assertRedirects(response, self.url)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Action de workflow inconnue", str(messages[0]))
