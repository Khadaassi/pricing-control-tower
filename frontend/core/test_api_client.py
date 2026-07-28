from unittest.mock import Mock, patch

import jwt
import requests
from django.test import TestCase, override_settings

from services.api_client import (
    ApiConnectionError,
    ApiResponseError,
    api_get,
    api_patch,
    api_post,
    build_user_headers,
    extract_api_error_message,
)


@override_settings(INTERNAL_AUTH_SECRET="test-internal-auth-secret")
class BuildUserHeadersTests(TestCase):
    def test_returns_empty_dict_without_user_email(self):
        self.assertEqual(build_user_headers(None), {})
        self.assertEqual(build_user_headers(""), {})

    def test_returns_signed_bearer_token_with_user_email(self):
        headers = build_user_headers("someone@pct.local")

        self.assertIn("Authorization", headers)
        self.assertTrue(headers["Authorization"].startswith("Bearer "))

        token = headers["Authorization"].removeprefix("Bearer ")
        payload = jwt.decode(token, "test-internal-auth-secret", algorithms=["HS256"])
        self.assertEqual(payload["sub"], "someone@pct.local")


def make_response(status_code=200, json_data=None, raise_exc=None):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    if raise_exc is not None:
        response.raise_for_status.side_effect = raise_exc
    else:
        response.raise_for_status.return_value = None
    return response


@override_settings(FASTAPI_BASE_URL="http://backend.test")
class ApiGetTests(TestCase):
    @patch("services.api_client.requests.get")
    def test_returns_json_on_success(self, mock_get):
        mock_get.return_value = make_response(200, {"items": [1, 2, 3]})

        result = api_get("/prices", params={"limit": 10}, user_email="a@b.com")

        self.assertEqual(result, {"items": [1, 2, 3]})
        called_url = mock_get.call_args.args[0]
        self.assertEqual(called_url, "http://backend.test/prices")
        self.assertIn("Authorization", mock_get.call_args.kwargs["headers"])

    @patch("services.api_client.requests.get")
    def test_connection_error_raises_api_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("refused")

        with self.assertRaises(ApiConnectionError):
            api_get("/prices")

    @patch("services.api_client.requests.get")
    def test_timeout_raises_api_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("too slow")

        with self.assertRaises(ApiConnectionError):
            api_get("/prices")

    @patch("services.api_client.requests.get")
    def test_http_error_raises_api_response_error_with_detail_message(self, mock_get):
        response = make_response(
            403,
            {"detail": "Permission denied: CREATE_PRICE_REQUEST is required"},
        )
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
        mock_get.return_value = response

        with self.assertRaises(ApiResponseError) as ctx:
            api_get("/price-change-requests")

        self.assertEqual(
            str(ctx.exception),
            "Permission denied: CREATE_PRICE_REQUEST is required",
        )

    @patch("services.api_client.requests.get")
    def test_invalid_json_raises_api_response_error(self, mock_get):
        response = make_response(200)
        response.json.side_effect = requests.exceptions.JSONDecodeError("boom", "doc", 0)
        mock_get.return_value = response

        with self.assertRaises(ApiResponseError):
            api_get("/prices")


@override_settings(FASTAPI_BASE_URL="http://backend.test")
class ApiPostTests(TestCase):
    @patch("services.api_client.requests.post")
    def test_returns_json_on_success(self, mock_post):
        mock_post.return_value = make_response(201, {"id": 1, "status": "PENDING"})

        result = api_post(
            "/price-change-requests",
            payload={"product_id": 1},
            user_email="a@b.com",
        )

        self.assertEqual(result, {"id": 1, "status": "PENDING"})
        self.assertEqual(mock_post.call_args.kwargs["json"], {"product_id": 1})

    @patch("services.api_client.requests.post")
    def test_http_error_raises_api_response_error(self, mock_post):
        response = make_response(409, {"detail": "Only PENDING requests can be approved"})
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
        mock_post.return_value = response

        with self.assertRaises(ApiResponseError) as ctx:
            api_post("/price-change-requests/1/approve")

        self.assertEqual(str(ctx.exception), "Only PENDING requests can be approved")


@override_settings(FASTAPI_BASE_URL="http://backend.test")
class ApiPatchTests(TestCase):
    @patch("services.api_client.requests.patch")
    def test_returns_json_on_success(self, mock_patch):
        mock_patch.return_value = make_response(200, {"id": 1, "active": False})

        result = api_patch("/promotions/1/deactivate", user_email="a@b.com")

        self.assertEqual(result, {"id": 1, "active": False})

    @patch("services.api_client.requests.patch")
    def test_connection_error_raises_api_connection_error(self, mock_patch):
        mock_patch.side_effect = requests.exceptions.ConnectionError("refused")

        with self.assertRaises(ApiConnectionError):
            api_patch("/promotions/1/deactivate")


class ExtractApiErrorMessageTests(TestCase):
    def test_string_detail(self):
        response = make_response(400, {"detail": "Bad input"})
        self.assertEqual(extract_api_error_message(response), "Bad input")

    def test_list_of_validation_errors(self):
        response = make_response(
            422,
            {
                "detail": [
                    {"loc": ["body", "product_id"], "msg": "field required"},
                    {"loc": ["body", "amount"], "msg": "must be positive"},
                ]
            },
        )
        message = extract_api_error_message(response)
        self.assertIn("product_id: field required", message)
        self.assertIn("amount: must be positive", message)

    def test_unparseable_body_falls_back_to_status_code(self):
        response = make_response(500)
        response.json.side_effect = requests.exceptions.JSONDecodeError("boom", "doc", 0)
        message = extract_api_error_message(response)
        self.assertIn("500", message)
