from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.services.ai_chatbot_client import AiChatbotConnectionError, AiChatbotResponseError


class ChatbotViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="store_manager",
            password="Password123!",
            email="store.manager@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:chatbot")

    def post_ajax(self, message):
        return self.client.post(
            self.url,
            {"message": message},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    @patch("core.views.ask_chatbot")
    def test_successful_answer_is_stored_and_returned(self, mock_ask_chatbot):
        mock_ask_chatbot.return_value = {
            "answer": "Un store manager peut consulter son magasin.",
            "status": "routed",
            "selected_tool": "rbac_tool",
            "metadata": {},
        }

        response = self.post_ajax("Que peut faire un store manager ?")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["assistant"]["status"], "routed")
        self.assertEqual(data["assistant"]["selected_tool"], "rbac_tool")
        self.assertIn("consulter son magasin", data["assistant"]["content"])

        history = self.client.session["chatbot_history"]
        self.assertEqual(history[-2], {"role": "user", "content": "Que peut faire un store manager ?"})
        self.assertEqual(history[-1]["status"], "routed")

    @patch("core.views.ask_chatbot")
    def test_connection_error_returns_clean_message_no_internals(self, mock_ask_chatbot):
        mock_ask_chatbot.side_effect = AiChatbotConnectionError("Connection refused")

        response = self.post_ajax("Une question")

        data = response.json()["assistant"]
        self.assertEqual(data["status"], "error")
        self.assertIsNone(data["selected_tool"])
        self.assertIn("momentanément indisponible", data["content"])
        self.assertNotIn("Connection refused", data["content"])

    @patch("core.views.ask_chatbot")
    def test_response_error_returns_clean_message_no_internals(self, mock_ask_chatbot):
        mock_ask_chatbot.side_effect = AiChatbotResponseError("JSONDecodeError: boom")

        response = self.post_ajax("Une question")

        data = response.json()["assistant"]
        self.assertEqual(data["status"], "error")
        self.assertIn("réponse inattendue", data["content"])
        self.assertNotIn("JSONDecodeError", data["content"])

    @patch("core.views.ask_chatbot")
    def test_unexpected_exception_returns_generic_message_no_traceback(self, mock_ask_chatbot):
        mock_ask_chatbot.side_effect = ValueError("unexpected internal bug")

        response = self.post_ajax("Une question")

        data = response.json()["assistant"]
        self.assertEqual(data["status"], "error")
        self.assertIn("erreur technique", data["content"])
        self.assertNotIn("unexpected internal bug", data["content"])
        self.assertNotIn("Traceback", data["content"])

    @patch("core.views.ask_chatbot")
    def test_empty_question_does_not_call_ai_service(self, mock_ask_chatbot):
        response = self.post_ajax("   ")

        self.assertEqual(response.status_code, 400)
        mock_ask_chatbot.assert_not_called()
