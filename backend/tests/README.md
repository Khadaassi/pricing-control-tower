# Backend automated tests

_Last verified: 2026-08-24_

This directory contains automated tests for the FastAPI backend.

## Structure

`backend/tests/` contains 7 test files (~40 `test_*` functions):

- `conftest.py`: shared pytest fixtures.
- `test_health.py`: basic healthcheck test.
- `test_analytics_and_history_auth.py`: RBAC/scope enforcement on analytics and price-history endpoints.
- `test_critical_endpoints.py`: smoke coverage of critical API endpoints.
- `test_price_change_request_concurrency.py`: concurrency handling on the price change request workflow.
- `test_price_change_request_workflow.py`: creation, approval/application, rejection, price history creation (see section below).
- `test_rbac_permissions.py`: RBAC permission checks.
- `test_scope_enforcement.py`: country/store scope enforcement.

## Run tests locally

```bash
uv run pytest
```

## Price change request workflow tests

These tests cover the main pricing workflow:
- request creation
- approval and application
- rejection
- price history creation