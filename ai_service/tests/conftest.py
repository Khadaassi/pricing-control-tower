from unittest.mock import MagicMock

import pytest

from app.clients.backend_client import BackendClient
from app.core.metrics import reset_metrics
from app.tools.anomaly_tool import AnomalyTool
from app.tools.business_rules_tool import BusinessRulesTool
from app.tools.kpi_tool import KPITool
from app.tools.price_change_request_tool import PriceChangeRequestTool
from app.tools.price_tool import PriceTool
from app.tools.promotion_tool import PromotionTool
from app.tools.rbac_tool import RBACTool
from app.tools.reference_data_tool import ReferenceDataTool


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    reset_metrics()
    yield
    reset_metrics()


@pytest.fixture
def mock_backend_client() -> MagicMock:
    return MagicMock(spec=BackendClient)


@pytest.fixture
def kpi_tool() -> KPITool:
    return KPITool()


@pytest.fixture
def business_rules_tool() -> BusinessRulesTool:
    return BusinessRulesTool()


@pytest.fixture
def rbac_tool() -> RBACTool:
    return RBACTool()


@pytest.fixture
def anomaly_tool(mock_backend_client: MagicMock) -> AnomalyTool:
    return AnomalyTool(backend_client=mock_backend_client)


@pytest.fixture
def reference_data_tool(mock_backend_client: MagicMock) -> ReferenceDataTool:
    return ReferenceDataTool(backend_client=mock_backend_client)


@pytest.fixture
def price_change_request_tool(mock_backend_client: MagicMock) -> PriceChangeRequestTool:
    return PriceChangeRequestTool(backend_client=mock_backend_client)


@pytest.fixture
def promotion_tool(mock_backend_client: MagicMock) -> PromotionTool:
    return PromotionTool(backend_client=mock_backend_client)


@pytest.fixture
def price_tool(mock_backend_client: MagicMock) -> PriceTool:
    return PriceTool(backend_client=mock_backend_client)
