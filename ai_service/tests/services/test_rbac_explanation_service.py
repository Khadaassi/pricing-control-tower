from unittest.mock import MagicMock

import pytest

from app.llm.base import BaseLLMProvider
from app.services.rbac_explanation_service import (
    _RBAC_LIST_ROLES_RESPONSE,
    _RBAC_LIST_ROLES_RESPONSE_FR,
    _RBAC_PERSONAL_RIGHTS_RESPONSE_FR,
    _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR,
    RBACExplanationService,
)
from app.tools.rbac_tool import RBACTool


@pytest.fixture
def mock_rbac_tool() -> MagicMock:
    return MagicMock(spec=RBACTool)


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    return MagicMock(spec=BaseLLMProvider)


@pytest.fixture
def service(mock_rbac_tool: MagicMock, mock_llm_provider: MagicMock) -> RBACExplanationService:
    return RBACExplanationService(
        rbac_tool=mock_rbac_tool,
        llm_provider=mock_llm_provider,
    )


class TestStaticRBACResponses:
    """Static responses are returned without calling the LLM or the RBAC tool search."""

    @pytest.mark.parametrize(
        "question,expected_response",
        [
            ("quels sont les différents rôles ?", _RBAC_LIST_ROLES_RESPONSE_FR),
            ("Quels sont les différents rôles ?", _RBAC_LIST_ROLES_RESPONSE_FR),
            ("quels sont les rôles", _RBAC_LIST_ROLES_RESPONSE_FR),
            ("liste des rôles", _RBAC_LIST_ROLES_RESPONSE_FR),
            ("liste des roles", _RBAC_LIST_ROLES_RESPONSE_FR),
            ("rôles rbac", _RBAC_LIST_ROLES_RESPONSE_FR),
            ("list roles", _RBAC_LIST_ROLES_RESPONSE),
            ("available roles", _RBAC_LIST_ROLES_RESPONSE),
        ],
    )
    def test_list_roles_returns_static_response(
        self,
        service: RBACExplanationService,
        mock_rbac_tool: MagicMock,
        mock_llm_provider: MagicMock,
        question: str,
        expected_response: str,
    ) -> None:
        result = service.explain(question)

        assert result["answer"] == expected_response
        assert result["source"] == "rbac_tool"
        assert result["llm_used"] is False
        assert result["roles_used"] == []
        mock_rbac_tool.search_rbac_rules.assert_not_called()
        mock_llm_provider.generate_response.assert_not_called()

    def test_list_roles_response_contains_four_roles(
        self, service: RBACExplanationService
    ) -> None:
        result = service.explain("quels sont les différents rôles ?")

        answer = result["answer"]
        assert "STORE_MANAGER" in answer
        assert "STORE_DIRECTOR" in answer
        assert "COUNTRY_DIRECTOR" in answer
        assert "PRICING_ANALYST" in answer

    @pytest.mark.parametrize(
        "question,expected_response",
        [
            ("Quels sont mes droits ?", _RBAC_PERSONAL_RIGHTS_RESPONSE_FR),
            ("quels sont mes droits", _RBAC_PERSONAL_RIGHTS_RESPONSE_FR),
            ("mes droits", _RBAC_PERSONAL_RIGHTS_RESPONSE_FR),
            ("mes permissions", _RBAC_PERSONAL_RIGHTS_RESPONSE_FR),
            ("quelles sont mes permissions", _RBAC_PERSONAL_RIGHTS_RESPONSE_FR),
        ],
    )
    def test_personal_rights_returns_static_response(
        self,
        service: RBACExplanationService,
        mock_rbac_tool: MagicMock,
        mock_llm_provider: MagicMock,
        question: str,
        expected_response: str,
    ) -> None:
        result = service.explain(question)

        assert result["answer"] == expected_response
        assert result["source"] == "rbac_tool"
        assert result["llm_used"] is False
        assert result["roles_used"] == []
        mock_rbac_tool.search_rbac_rules.assert_not_called()
        mock_llm_provider.generate_response.assert_not_called()

    def test_personal_rights_response_is_cautious(
        self, service: RBACExplanationService
    ) -> None:
        result = service.explain("Quels sont mes droits ?")

        answer = result["answer"]
        # FR question → FR response
        assert "ne peux pas déterminer" in answer or "cannot determine" in answer
        assert "backend" in answer

    @pytest.mark.parametrize(
        "question,expected_response",
        [
            ("Quels sont mes droits sur le pricing workflow ?", _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR),
            ("droits sur le pricing workflow", _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR),
            ("permissions sur le pricing workflow", _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR),
            ("droits sur le workflow", _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR),
        ],
    )
    def test_workflow_rights_returns_static_response(
        self,
        service: RBACExplanationService,
        mock_rbac_tool: MagicMock,
        mock_llm_provider: MagicMock,
        question: str,
        expected_response: str,
    ) -> None:
        result = service.explain(question)

        assert result["answer"] == expected_response
        assert result["source"] == "rbac_tool"
        assert result["llm_used"] is False
        assert result["roles_used"] == []
        mock_rbac_tool.search_rbac_rules.assert_not_called()
        mock_llm_provider.generate_response.assert_not_called()

    def test_workflow_rights_not_matched_as_personal_rights(
        self,
        service: RBACExplanationService,
    ) -> None:
        # "mes droits sur le pricing workflow" contains "mes droits" — workflow must win.
        result = service.explain("Quels sont mes droits sur le pricing workflow ?")

        assert result["answer"] == _RBAC_WORKFLOW_RIGHTS_RESPONSE_FR

    def test_specific_role_question_falls_through_to_llm(
        self,
        service: RBACExplanationService,
        mock_rbac_tool: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_rbac_tool.search_rbac_rules.return_value = {
            "found": True,
            "roles": [{"role_code": "STORE_MANAGER", "label": "Store Manager", "scope": "store"}],
        }
        mock_llm_provider.generate_response.return_value = "Le Store Manager accède à son magasin."

        result = service.explain("Que peut faire un store manager ?")

        mock_rbac_tool.search_rbac_rules.assert_called_once()
        mock_llm_provider.generate_response.assert_called_once()
        assert result["llm_used"] is True
