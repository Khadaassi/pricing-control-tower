import pytest
from fastapi.testclient import TestClient

from app.main import app

def test_health_endpoint_returns_success(client):
    response = client.get("/health")

    assert response.status_code == 200