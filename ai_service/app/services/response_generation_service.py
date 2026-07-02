from app.core.chatbot_messages import (
    CHATBOT_AMBIGUOUS_QUESTION_MESSAGE,
    CHATBOT_AMBIGUOUS_QUESTION_MESSAGE_FR,
    CHATBOT_GUARDRAIL_ACTION_MESSAGE,
    CHATBOT_GUARDRAIL_ACTION_MESSAGE_FR,
    CHATBOT_OUT_OF_SCOPE_MESSAGE,
    CHATBOT_OUT_OF_SCOPE_MESSAGE_FR,
)


class ResponseGenerationService:
    """Centralises response formatting for all chatbot answer types."""

    def format_tool_response(
        self,
        summary: str,
        details: list[str],
        suggested_next_step: str | None = None,
        lang: str = "fr",
    ) -> str:
        if lang == "fr":
            lines = ["Résumé :", summary, "", "Détails :"]
            lines += [f"- {d}" for d in details]
            if suggested_next_step:
                lines += ["", "Prochaine étape suggérée :", suggested_next_step]
        else:
            lines = ["Summary:", summary, "", "Details:"]
            lines += [f"- {d}" for d in details]
            if suggested_next_step:
                lines += ["", "Suggested next step:", suggested_next_step]
        return "\n".join(lines)

    def format_guardrail_response(self, lang: str = "en") -> str:
        return CHATBOT_GUARDRAIL_ACTION_MESSAGE_FR if lang == "fr" else CHATBOT_GUARDRAIL_ACTION_MESSAGE

    def format_clarification_response(self, message: str | None = None, lang: str = "en") -> str:
        if message is not None:
            return message
        return CHATBOT_AMBIGUOUS_QUESTION_MESSAGE_FR if lang == "fr" else CHATBOT_AMBIGUOUS_QUESTION_MESSAGE

    def format_fallback_response(self, lang: str = "en") -> str:
        return CHATBOT_OUT_OF_SCOPE_MESSAGE_FR if lang == "fr" else CHATBOT_OUT_OF_SCOPE_MESSAGE
