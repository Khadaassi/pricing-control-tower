# Backend automated tests

This directory contains automated tests for the FastAPI backend.

## Structure

- `conftest.py`: shared pytest fixtures.
- `test_health.py`: basic healthcheck test.
- Future test files will cover:
  - pricing workflow
  - RBAC permissions
  - critical API endpoints

## Run tests locally

```bash
uv run pytest

## Price change request workflow tests

These tests cover the main pricing workflow:
- request creation
- approval and application
- rejection
- price history creation