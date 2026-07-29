import logging
import time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from core.chatbot_suggestions import get_chatbot_suggestions
from core.services.ai_chatbot_client import (
    AiChatbotConnectionError,
    AiChatbotResponseError,
    ask_chatbot,
)

logger = logging.getLogger("pricing_control_tower.frontend.chatbot")


class ChatbotView(LoginRequiredMixin, TemplateView):
    """Chatbot UI: forwards questions to the AI service and displays its
    response. No intent detection, tool selection or KPI/RBAC/anomaly
    interpretation here — that logic lives entirely in ai_service."""

    template_name = "core/chatbot.html"

    CONNECTION_ERROR_REPLY = "Le service IA est momentanément indisponible. Veuillez réessayer plus tard."
    RESPONSE_ERROR_REPLY = "Le service IA a retourné une réponse inattendue. Veuillez réessayer."
    TECHNICAL_ERROR_REPLY = "Une erreur technique est survenue pendant l'appel au chatbot."
    EXAMPLE_QUESTIONS = [
        "Explique le chiffre d'affaires.",
        "Que peut faire un store manager ?",
        "Explique les anomalies du magasin 1.",
        "Le chatbot peut-il approuver une demande de changement de prix ?",
    ]

    MAX_HISTORY_TURNS = 20
    MAX_MESSAGE_LENGTH = 4000
    # chatbot_history can surface pricing data via tool answers — don't keep it around
    # indefinitely regardless of the session's own (much longer) expiry.
    HISTORY_TTL_SECONDS = 60 * 60

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chatbot_history"] = self._get_valid_history(self.request)
        page = self.request.GET.get("page")
        context["chatbot_suggestions"] = get_chatbot_suggestions(page)
        context["example_questions"] = self.EXAMPLE_QUESTIONS
        return context

    def post(self, request, *args, **kwargs):
        question = request.POST.get("message", "").strip()
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not question:
            if is_ajax:
                return JsonResponse({"error": "empty_question"}, status=400)
            return redirect("core:chatbot")

        question = self._truncate(question)

        history = self._get_valid_history(request)
        history.append({"role": "user", "content": question})
        assistant_turn = self._get_assistant_turn(request, question)
        assistant_turn["content"] = self._truncate(assistant_turn["content"])
        history.append(assistant_turn)

        request.session["chatbot_history"] = history[-self.MAX_HISTORY_TURNS:]
        request.session["chatbot_history_updated_at"] = time.time()

        if is_ajax:
            return JsonResponse({"assistant": assistant_turn})

        return redirect("core:chatbot")

    def _get_valid_history(self, request) -> list[dict]:
        updated_at = request.session.get("chatbot_history_updated_at")

        if updated_at is not None and time.time() - updated_at > self.HISTORY_TTL_SECONDS:
            request.session.pop("chatbot_history", None)
            request.session.pop("chatbot_history_updated_at", None)
            return []

        return request.session.get("chatbot_history", [])

    @classmethod
    def _truncate(cls, text: str) -> str:
        if len(text) <= cls.MAX_MESSAGE_LENGTH:
            return text

        return text[: cls.MAX_MESSAGE_LENGTH] + "…"

    def _get_assistant_turn(self, request, question: str) -> dict:
        try:
            result = ask_chatbot(
                question=question,
                user_email=request.user.email or None,
                store_id=request.session.get("store_id"),
            )
        except AiChatbotConnectionError:
            return self._error_turn(self.CONNECTION_ERROR_REPLY)
        except AiChatbotResponseError:
            return self._error_turn(self.RESPONSE_ERROR_REPLY)
        except Exception:
            logger.exception("Unexpected error while calling the AI service")
            return self._error_turn(self.TECHNICAL_ERROR_REPLY)

        metadata = result.get("metadata") or {}

        return {
            "role": "assistant",
            "content": result.get("answer") or metadata.get("message") or self.TECHNICAL_ERROR_REPLY,
            "status": result.get("status"),
            "selected_tool": result.get("selected_tool"),
        }

    @staticmethod
    def _error_turn(content: str) -> dict:
        return {
            "role": "assistant",
            "content": content,
            "status": "error",
            "selected_tool": None,
        }
