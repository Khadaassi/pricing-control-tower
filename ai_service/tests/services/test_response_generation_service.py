import pytest

from app.core.chatbot_messages import (
    CHATBOT_AMBIGUOUS_QUESTION_MESSAGE,
    CHATBOT_PRICE_CLARIFICATION_MESSAGE,
    CHATBOT_STORE_CLARIFICATION_MESSAGE,
)
from app.services.response_generation_service import ResponseGenerationService


@pytest.fixture
def service() -> ResponseGenerationService:
    return ResponseGenerationService()


# ---------------------------------------------------------------------------
# format_tool_response
# ---------------------------------------------------------------------------


class TestFormatToolResponse:
    def test_output_contains_summary_label(self, service: ResponseGenerationService) -> None:
        result = service.format_tool_response(summary="3 résultats trouvés.", details=["Item A"])

        assert "Résumé :" in result

    def test_output_contains_summary_text(self, service: ResponseGenerationService) -> None:
        result = service.format_tool_response(summary="3 résultats trouvés.", details=["Item A"])

        assert "3 résultats trouvés." in result

    def test_output_contains_details_label(self, service: ResponseGenerationService) -> None:
        result = service.format_tool_response(summary="1 item.", details=["Item A"])

        assert "Détails :" in result

    def test_each_detail_line_has_bullet_prefix(self, service: ResponseGenerationService) -> None:
        result = service.format_tool_response(
            summary="2 items.", details=["Item A", "Item B"]
        )

        assert "- Item A" in result
        assert "- Item B" in result

    def test_multiple_details_all_present(self, service: ResponseGenerationService) -> None:
        result = service.format_tool_response(
            summary="3 items.", details=["Alpha", "Beta", "Gamma"]
        )

        assert "Alpha" in result
        assert "Beta" in result
        assert "Gamma" in result

    def test_suggested_next_step_included_when_provided(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_tool_response(
            summary="1 item.",
            details=["Item A"],
            suggested_next_step="Vérifiez avant de valider.",
        )

        assert "Prochaine étape suggérée :" in result
        assert "Vérifiez avant de valider." in result

    def test_suggested_next_step_absent_when_none(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_tool_response(
            summary="1 item.", details=["Item A"], suggested_next_step=None
        )

        assert "Prochaine étape suggérée :" not in result

    def test_suggested_next_step_absent_by_default(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_tool_response(summary="1 item.", details=["Item A"])

        assert "Prochaine étape suggérée :" not in result

    def test_summary_appears_before_details(self, service: ResponseGenerationService) -> None:
        result = service.format_tool_response(
            summary="Le résumé.", details=["Le détail."]
        )

        assert result.index("Résumé :") < result.index("Détails :")

    def test_details_appear_before_suggested_next_step(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_tool_response(
            summary="S.",
            details=["D."],
            suggested_next_step="Prochaine étape.",
        )

        assert result.index("Détails :") < result.index("Prochaine étape suggérée :")

    def test_no_forbidden_action_verbs_in_next_step(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_tool_response(
            summary="1 item.",
            details=["Item A"],
            suggested_next_step="Review the related request before deciding.",
        )

        forbidden = ["apply now", "approve now", "reject now", "delete now"]
        for phrase in forbidden:
            assert phrase not in result.lower()


# ---------------------------------------------------------------------------
# format_guardrail_response
# ---------------------------------------------------------------------------


class TestFormatGuardrailResponse:
    def test_refuses_direct_action(self, service: ResponseGenerationService) -> None:
        result = service.format_guardrail_response()

        assert "cannot" in result.lower() or "can not" in result.lower()

    def test_offers_safe_alternatives(self, service: ResponseGenerationService) -> None:
        result = service.format_guardrail_response()

        assert "explain" in result.lower() or "workflow" in result.lower()

    def test_does_not_propose_write_action(self, service: ResponseGenerationService) -> None:
        result = service.format_guardrail_response()

        assert "approve" not in result.lower()
        assert "reject" not in result.lower()
        assert "apply" not in result.lower()

    def test_is_non_empty(self, service: ResponseGenerationService) -> None:
        assert service.format_guardrail_response()


# ---------------------------------------------------------------------------
# format_clarification_response
# ---------------------------------------------------------------------------


class TestFormatClarificationResponse:
    def test_asks_for_missing_detail(self, service: ResponseGenerationService) -> None:
        result = service.format_clarification_response()

        assert "detail" in result.lower() or "asking about" in result.lower()

    def test_mentions_operational_data(self, service: ResponseGenerationService) -> None:
        result = service.format_clarification_response()

        assert "operational" in result.lower() or "prices" in result.lower()

    def test_mentions_reference_data(self, service: ResponseGenerationService) -> None:
        result = service.format_clarification_response()

        assert "reference" in result.lower() or "stores" in result.lower()

    def test_mentions_documentation(self, service: ResponseGenerationService) -> None:
        result = service.format_clarification_response()

        assert "documentation" in result.lower() or "rules" in result.lower()

    def test_is_non_empty(self, service: ResponseGenerationService) -> None:
        assert service.format_clarification_response()


# ---------------------------------------------------------------------------
# format_clarification_response — with targeted message (T203)
# ---------------------------------------------------------------------------


class TestFormatClarificationResponseWithMessage:
    def test_custom_message_is_returned_verbatim(
        self, service: ResponseGenerationService
    ) -> None:
        custom = "Please specify what you need."
        result = service.format_clarification_response(custom)

        assert result == custom

    def test_price_clarification_message_is_returned(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_clarification_response(CHATBOT_PRICE_CLARIFICATION_MESSAGE)

        assert result == CHATBOT_PRICE_CLARIFICATION_MESSAGE
        assert "prices" in result.lower() or "price" in result.lower()

    def test_store_clarification_message_is_returned(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_clarification_response(CHATBOT_STORE_CLARIFICATION_MESSAGE)

        assert result == CHATBOT_STORE_CLARIFICATION_MESSAGE
        assert "store" in result.lower()

    def test_none_falls_back_to_generic_message(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_clarification_response(None)

        assert result == CHATBOT_AMBIGUOUS_QUESTION_MESSAGE

    def test_no_arg_falls_back_to_generic_message(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_clarification_response()

        assert result == CHATBOT_AMBIGUOUS_QUESTION_MESSAGE


# ---------------------------------------------------------------------------
# format_fallback_response
# ---------------------------------------------------------------------------


class TestFormatFallbackResponse:
    def test_does_not_claim_to_answer(self, service: ResponseGenerationService) -> None:
        result = service.format_fallback_response()

        assert "cannot" in result.lower() or "can not" in result.lower()

    def test_lists_supported_topics(self, service: ResponseGenerationService) -> None:
        result = service.format_fallback_response()

        assert "prices" in result.lower()
        assert "promotions" in result.lower()
        assert "anomalies" in result.lower()

    def test_mentions_price_change_requests(self, service: ResponseGenerationService) -> None:
        result = service.format_fallback_response()

        assert "price change" in result.lower()

    def test_mentions_documentation(self, service: ResponseGenerationService) -> None:
        result = service.format_fallback_response()

        assert "documentation" in result.lower()

    def test_is_non_empty(self, service: ResponseGenerationService) -> None:
        assert service.format_fallback_response()

    def test_does_not_hallucinate_unsupported_topics(
        self, service: ResponseGenerationService
    ) -> None:
        result = service.format_fallback_response()

        assert "supplier" not in result.lower()
        assert "invoice" not in result.lower()
