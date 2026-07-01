from app.core.chatbot_messages import (
    CHATBOT_AMBIGUOUS_QUESTION_MESSAGE,
    CHATBOT_GUARDRAIL_ACTION_MESSAGE,
    CHATBOT_OUT_OF_SCOPE_MESSAGE,
)


class ResponseGenerationService:
    """Centralises response formatting for all chatbot answer types.

    Tool-calling responses follow a Summary / Details / Suggested next step
    structure.  Static responses (guardrail, clarification, fallback) delegate
    to the constants in chatbot_messages so there is a single source of truth.
    """

    def format_tool_response(
        self,
        summary: str,
        details: list[str],
        suggested_next_step: str | None = None,
    ) -> str:
        lines = ["Summary:", summary, "", "Details:"]
        lines += [f"- {d}" for d in details]
        if suggested_next_step:
            lines += ["", "Suggested next step:", suggested_next_step]
        return "\n".join(lines)

    def format_guardrail_response(self) -> str:
        return CHATBOT_GUARDRAIL_ACTION_MESSAGE

    def format_clarification_response(self) -> str:
        return CHATBOT_AMBIGUOUS_QUESTION_MESSAGE

    def format_fallback_response(self) -> str:
        return CHATBOT_OUT_OF_SCOPE_MESSAGE
