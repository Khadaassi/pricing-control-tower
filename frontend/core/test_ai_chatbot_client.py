from unittest.mock import Mock, patch

import jwt
import requests
from django.conf import settings
from django.test import TestCase, override_settings

from core.services.ai_chatbot_client import (
    AiChatbotConnectionError,
    AiChatbotResponseError,
    ask_chatbot,
    build_chat_payload,
)


class BuildChatPayloadTests(TestCase):
    def test_minimal_payload_has_only_question(self):
        payload = build_chat_payload("Quel est le chiffre d'affaires ?")
        self.assertEqual(payload, {"question": "Quel est le chiffre d'affaires ?"})

    def test_includes_user_email_when_present(self):
        payload = build_chat_payload("question", user_email="a@b.com")
        self.assertEqual(payload["user_email"], "a@b.com")

    def test_includes_positive_store_id_only(self):
        payload = build_chat_payload("question", store_id=5)
        self.assertEqual(payload["store_id"], 5)

        payload_no_store = build_chat_payload("question", store_id=0)
        self.assertNotIn("store_id", payload_no_store)

        payload_bad_type = build_chat_payload("question", store_id="not-an-int")
        self.assertNotIn("store_id", payload_bad_type)


def make_response(status_code=200, json_data=None, raise_exc=None):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = json_data
    if raise_exc is not None:
        response.raise_for_status.side_effect = raise_exc
    else:
        response.raise_for_status.return_value = None
    return response


# ask_chatbot() now funnels through services.http.do_request, which calls
# requests.request(method, url, ...) — that's the single point to mock.
@override_settings(AI_SERVICE_BASE_URL="http://ai-service.test")
class AskChatbotTests(TestCase):
    @patch("services.http.requests.request")
    def test_returns_json_on_success(self, mock_request):
        mock_request.return_value = make_response(
            200,
            {"answer": "42", "status": "routed", "selected_tool": "kpi_tool"},
        )

        result = ask_chatbot("question", user_email="a@b.com", store_id=3)

        self.assertEqual(result["answer"], "42")
        self.assertEqual(mock_request.call_args.args, ("POST", "http://ai-service.test/chat"))
        self.assertEqual(
            mock_request.call_args.kwargs["json"],
            {"question": "question", "user_email": "a@b.com", "store_id": 3},
        )

    @patch("services.http.requests.request")
    def test_sends_signed_service_bearer_token(self, mock_request):
        mock_request.return_value = make_response(200, {"answer": "ok", "status": "answered"})

        ask_chatbot("question")

        auth_header = mock_request.call_args.kwargs["headers"]["Authorization"]
        self.assertTrue(auth_header.startswith("Bearer "))

        token = auth_header.removeprefix("Bearer ")
        payload = jwt.decode(token, settings.INTERNAL_AUTH_SECRET, algorithms=["HS256"])
        self.assertEqual(payload["sub"], "pricing-control-tower-frontend")

    @patch("services.http.requests.request")
    def test_connection_error_raises_ai_chatbot_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError("refused")

        with self.assertRaises(AiChatbotConnectionError):
            ask_chatbot("question")

    @patch("services.http.requests.request")
    def test_timeout_raises_ai_chatbot_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.Timeout("too slow")

        with self.assertRaises(AiChatbotConnectionError):
            ask_chatbot("question")

    @patch("services.http.requests.request")
    def test_http_error_raises_ai_chatbot_response_error(self, mock_request):
        response = make_response(500)
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
        mock_request.return_value = response

        with self.assertRaises(AiChatbotResponseError) as ctx:
            ask_chatbot("question")

        self.assertIn("500", str(ctx.exception))

    @patch("services.http.requests.request")
    def test_invalid_json_raises_ai_chatbot_response_error(self, mock_request):
        response = make_response(200)
        response.json.side_effect = requests.exceptions.JSONDecodeError("boom", "doc", 0)
        mock_request.return_value = response

        with self.assertRaises(AiChatbotResponseError):
            ask_chatbot("question")
