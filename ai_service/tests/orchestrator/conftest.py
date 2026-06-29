from unittest.mock import MagicMock

import pytest

from app.orchestrator.chatbot_orchestrator import ChatbotOrchestrator
from app.services.business_rules_explanation_service import (
    BusinessRulesExplanationService,
)
from app.services.kpi_explanation_service import KPIExplanationService
from app.services.rbac_explanation_service import RBACExplanationService
from app.tools.anomaly_tool import AnomalyTool


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
def orchestrator(
    mock_kpi_service: MagicMock,
    mock_rbac_service: MagicMock,
    mock_business_rules_service: MagicMock,
    mock_anomaly_tool: MagicMock,
) -> ChatbotOrchestrator:
    return ChatbotOrchestrator(
        business_rules_service=mock_business_rules_service,
        rbac_service=mock_rbac_service,
        anomaly_tool=mock_anomaly_tool,
        kpi_service=mock_kpi_service,
    )
