from unittest.mock import MagicMock

import pytest

from app.clients.backend_client import BackendClient
from app.core.metrics import reset_metrics
from app.tools.anomaly_tool import AnomalyTool
from app.tools.business_rules_tool import BusinessRulesTool
from app.tools.kpi_tool import KPITool
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
