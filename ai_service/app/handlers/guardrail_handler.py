"""Handler for guardrail-blocked requests.

The chatbot is read-only.  Any request that asks to perform a write action
(approve, reject, apply, modify, delete…) is intercepted here and returns a
fixed refusal message without calling any tool or the LLM.
"""

from typing import Any

from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import IntentMatch
from app.services.response_generation_service import ResponseGenerationService


class GuardrailHandler:
    def __init__(self, response_service: ResponseGenerationService) -> None:
        self._response_service = response_service

    def handle(self, ctx: ChatContext, match: IntentMatch) -> dict[str, Any]:
        return {
            "status": "guardrail",
            "answer": self._response_service.format_guardrail_response(lang=ctx.lang),
            "source": "orchestrator",
        }
