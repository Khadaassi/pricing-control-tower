from unittest.mock import MagicMock

import pytest

from app.llm.base import BaseLLMProvider
from app.orchestrator.chatbot_orchestrator import ChatbotOrchestrator
from app.rag.retriever import DocumentRetriever
from app.services.business_rules_explanation_service import (
    BusinessRulesExplanationService,
)
from app.services.kpi_explanation_service import KPIExplanationService
from app.services.rbac_explanation_service import RBACExplanationService
from app.tools.anomaly_tool import AnomalyTool
from app.tools.price_change_request_tool import PriceChangeRequestTool
from app.tools.price_tool import PriceTool
from app.tools.promotion_tool import PromotionTool
from app.tools.reference_data_tool import ReferenceDataTool


@pytest.fixture
def mock_kpi_service() -> MagicMock:
    return MagicMock(spec=KPIExplanationService)


@pytest.fixture
def mock_rbac_service() -> MagicMock:
    return MagicMock(spec=RBACExplanationService)


@pytest.fixture
def mock_business_rules_service() -> MagicMock:
    return MagicMock(spec=BusinessRulesExplanationService)


@pytest.fixture
def mock_anomaly_tool() -> MagicMock:
    return MagicMock(spec=AnomalyTool)


@pytest.fixture
def mock_reference_data_tool() -> MagicMock:
    return MagicMock(spec=ReferenceDataTool)


@pytest.fixture
def mock_price_change_request_tool() -> MagicMock:
    return MagicMock(spec=PriceChangeRequestTool)


@pytest.fixture
def mock_promotion_tool() -> MagicMock:
    return MagicMock(spec=PromotionTool)


@pytest.fixture
def mock_price_tool() -> MagicMock:
    return MagicMock(spec=PriceTool)


@pytest.fixture
def mock_document_retriever() -> MagicMock:
    return MagicMock(spec=DocumentRetriever)


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    return MagicMock(spec=BaseLLMProvider)


@pytest.fixture
def orchestrator(
    mock_kpi_service: MagicMock,
    mock_rbac_service: MagicMock,
    mock_business_rules_service: MagicMock,
    mock_anomaly_tool: MagicMock,
    mock_price_change_request_tool: MagicMock,
    mock_promotion_tool: MagicMock,
    mock_price_tool: MagicMock,
    mock_reference_data_tool: MagicMock,
    mock_document_retriever: MagicMock,
    mock_llm_provider: MagicMock,
) -> ChatbotOrchestrator:
    return ChatbotOrchestrator(
        business_rules_service=mock_business_rules_service,
        rbac_service=mock_rbac_service,
        anomaly_tool=mock_anomaly_tool,
        kpi_service=mock_kpi_service,
        price_change_request_tool=mock_price_change_request_tool,
        promotion_tool=mock_promotion_tool,
        price_tool=mock_price_tool,
        reference_data_tool=mock_reference_data_tool,
        document_retriever=mock_document_retriever,
        llm_provider=mock_llm_provider,
    )
