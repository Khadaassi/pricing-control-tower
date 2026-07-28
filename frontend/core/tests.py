import time
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

    @patch("core.views.chatbot.ask_chatbot")
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

    @patch("core.views.chatbot.ask_chatbot")
    def test_connection_error_returns_clean_message_no_internals(self, mock_ask_chatbot):
        mock_ask_chatbot.side_effect = AiChatbotConnectionError("Connection refused")

        response = self.post_ajax("Une question")

        data = response.json()["assistant"]
        self.assertEqual(data["status"], "error")
        self.assertIsNone(data["selected_tool"])
        self.assertIn("momentanément indisponible", data["content"])
        self.assertNotIn("Connection refused", data["content"])

    @patch("core.views.chatbot.ask_chatbot")
    def test_response_error_returns_clean_message_no_internals(self, mock_ask_chatbot):
        mock_ask_chatbot.side_effect = AiChatbotResponseError("JSONDecodeError: boom")

        response = self.post_ajax("Une question")

        data = response.json()["assistant"]
        self.assertEqual(data["status"], "error")
        self.assertIn("réponse inattendue", data["content"])
        self.assertNotIn("JSONDecodeError", data["content"])

    @patch("core.views.chatbot.ask_chatbot")
    def test_unexpected_exception_returns_generic_message_no_traceback(self, mock_ask_chatbot):
        mock_ask_chatbot.side_effect = ValueError("unexpected internal bug")

        response = self.post_ajax("Une question")

        data = response.json()["assistant"]
        self.assertEqual(data["status"], "error")
        self.assertIn("erreur technique", data["content"])
        self.assertNotIn("unexpected internal bug", data["content"])
        self.assertNotIn("Traceback", data["content"])

    @patch("core.views.chatbot.ask_chatbot")
    def test_empty_question_does_not_call_ai_service(self, mock_ask_chatbot):
        response = self.post_ajax("   ")

        self.assertEqual(response.status_code, 400)
        mock_ask_chatbot.assert_not_called()


class ChatbotHistoryLimitsTests(TestCase):
    """chatbot_history: per-message length cap and TTL-based expiry (may contain pricing
    data surfaced by tool answers, so it shouldn't linger indefinitely)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="history_limits_user",
            password="Password123!",
            email="history.limits@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:chatbot")

    def post_ajax(self, message):
        return self.client.post(
            self.url,
            {"message": message},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    @patch("core.views.chatbot.ask_chatbot")
    def test_long_user_message_is_truncated_before_storage(self, mock_ask_chatbot):
        mock_ask_chatbot.return_value = {
            "answer": "ok",
            "status": "routed",
            "selected_tool": None,
            "metadata": {},
        }

        long_message = "a" * 5000
        self.post_ajax(long_message)

        history = self.client.session["chatbot_history"]
        stored_question = history[-2]["content"]
        self.assertEqual(len(stored_question), 4001)  # MAX_MESSAGE_LENGTH + ellipsis
        self.assertTrue(stored_question.endswith("…"))

    @patch("core.views.chatbot.ask_chatbot")
    def test_long_assistant_reply_is_truncated_before_storage(self, mock_ask_chatbot):
        mock_ask_chatbot.return_value = {
            "answer": "b" * 5000,
            "status": "routed",
            "selected_tool": None,
            "metadata": {},
        }

        self.post_ajax("question")

        history = self.client.session["chatbot_history"]
        stored_answer = history[-1]["content"]
        self.assertEqual(len(stored_answer), 4001)
        self.assertTrue(stored_answer.endswith("…"))

    @patch("core.views.chatbot.ask_chatbot")
    def test_post_refreshes_history_updated_at(self, mock_ask_chatbot):
        mock_ask_chatbot.return_value = {
            "answer": "ok",
            "status": "routed",
            "selected_tool": None,
            "metadata": {},
        }

        self.post_ajax("question")

        self.assertIn("chatbot_history_updated_at", self.client.session)

    @patch("core.views.chatbot.ask_chatbot")
    def test_expired_history_is_cleared_on_next_post(self, mock_ask_chatbot):
        session = self.client.session
        session["chatbot_history"] = [{"role": "user", "content": "old pricing question"}]
        session["chatbot_history_updated_at"] = time.time() - 3601  # just past the 1h TTL
        session.save()

        mock_ask_chatbot.return_value = {
            "answer": "fresh answer",
            "status": "routed",
            "selected_tool": None,
            "metadata": {},
        }

        self.post_ajax("new question")

        history = self.client.session["chatbot_history"]
        # only the new turn should remain — the expired one was dropped, not carried forward
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["content"], "new question")

    def test_expired_history_is_cleared_on_page_load(self):
        session = self.client.session
        session["chatbot_history"] = [{"role": "user", "content": "old pricing question"}]
        session["chatbot_history_updated_at"] = time.time() - 3601
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.context["chatbot_history"], [])

    def test_fresh_history_is_kept_on_page_load(self):
        session = self.client.session
        session["chatbot_history"] = [{"role": "user", "content": "recent question"}]
        session["chatbot_history_updated_at"] = time.time() - 60
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["chatbot_history"]), 1)


# ---------------------------------------------------------------------------
# T204 — Chatbot contextual suggestions
# ---------------------------------------------------------------------------


class ChatbotSuggestionsUnitTests(TestCase):
    """Unit tests for the get_chatbot_suggestions helper."""

    def setUp(self):
        from core.chatbot_suggestions import (
            CHATBOT_SUGGESTIONS_BY_PAGE,
            get_chatbot_suggestions,
        )
        self.get = get_chatbot_suggestions
        self.pages = CHATBOT_SUGGESTIONS_BY_PAGE

    def test_dashboard_returns_dashboard_suggestions(self):
        result = self.get("dashboard")
        self.assertEqual(result, self.pages["dashboard"])

    def test_prices_returns_prices_suggestions(self):
        result = self.get("prices")
        self.assertEqual(result, self.pages["prices"])

    def test_promotions_returns_promotions_suggestions(self):
        result = self.get("promotions")
        self.assertEqual(result, self.pages["promotions"])

    def test_price_change_requests_returns_correct_suggestions(self):
        result = self.get("price_change_requests")
        self.assertEqual(result, self.pages["price_change_requests"])

    def test_anomalies_returns_anomalies_suggestions(self):
        result = self.get("anomalies")
        self.assertEqual(result, self.pages["anomalies"])

    def test_unknown_page_returns_default(self):
        result = self.get("unknown_page_xyz")
        self.assertEqual(result, self.pages["default"])

    def test_none_returns_default(self):
        result = self.get(None)
        self.assertEqual(result, self.pages["default"])

    def test_empty_string_returns_default(self):
        result = self.get("")
        self.assertEqual(result, self.pages["default"])

    def test_each_page_has_at_least_two_suggestions(self):
        for page, suggestions in self.pages.items():
            self.assertGreaterEqual(len(suggestions), 2, f"Page '{page}' has fewer than 2 suggestions")

    def test_each_page_has_at_most_three_suggestions(self):
        for page, suggestions in self.pages.items():
            self.assertLessEqual(len(suggestions), 3, f"Page '{page}' has more than 3 suggestions")

    def test_no_suggestion_is_empty(self):
        for page, suggestions in self.pages.items():
            for suggestion in suggestions:
                self.assertTrue(suggestion.strip(), f"Empty suggestion found on page '{page}'")


class ChatbotViewSuggestionsTests(TestCase):
    """View-level tests: chatbot page injects context-aware suggestions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="manager_t204",
            password="Password123!",
            email="manager.t204@pct.local",
        )
        self.client.force_login(self.user)
        self.url = reverse("core:chatbot")

    def test_chatbot_page_has_default_suggestions_without_page_param(self):
        from core.chatbot_suggestions import CHATBOT_SUGGESTIONS_BY_PAGE
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["chatbot_suggestions"],
            CHATBOT_SUGGESTIONS_BY_PAGE["default"],
        )

    def test_chatbot_page_loads_prices_suggestions_with_page_param(self):
        from core.chatbot_suggestions import CHATBOT_SUGGESTIONS_BY_PAGE
        response = self.client.get(self.url + "?page=prices")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["chatbot_suggestions"],
            CHATBOT_SUGGESTIONS_BY_PAGE["prices"],
        )

    def test_chatbot_page_loads_promotions_suggestions_with_page_param(self):
        from core.chatbot_suggestions import CHATBOT_SUGGESTIONS_BY_PAGE
        response = self.client.get(self.url + "?page=promotions")
        self.assertEqual(
            response.context["chatbot_suggestions"],
            CHATBOT_SUGGESTIONS_BY_PAGE["promotions"],
        )

    def test_chatbot_page_loads_price_change_requests_suggestions(self):
        from core.chatbot_suggestions import CHATBOT_SUGGESTIONS_BY_PAGE
        response = self.client.get(self.url + "?page=price_change_requests")
        self.assertEqual(
            response.context["chatbot_suggestions"],
            CHATBOT_SUGGESTIONS_BY_PAGE["price_change_requests"],
        )

    def test_chatbot_page_falls_back_to_default_for_unknown_page(self):
        from core.chatbot_suggestions import CHATBOT_SUGGESTIONS_BY_PAGE
        response = self.client.get(self.url + "?page=nonexistent")
        self.assertEqual(
            response.context["chatbot_suggestions"],
            CHATBOT_SUGGESTIONS_BY_PAGE["default"],
        )

    def test_suggestion_buttons_rendered_in_template(self):
        response = self.client.get(self.url)
        self.assertContains(response, "chatbot-suggestion-btn")

    def test_suggestion_buttons_have_data_question_attribute(self):
        response = self.client.get(self.url)
        self.assertContains(response, "data-question=")
