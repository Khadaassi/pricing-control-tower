from datetime import datetime


def test_health_endpoint_returns_success(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in ["ok", "degraded"]
    assert data["service"] == "pricing-control-tower-api"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]

    database = data["checks"]["database"]

    assert database["status"] in ["ok", "error"]
    assert database["type"] == "postgresql"

    datetime.fromisoformat(data["timestamp"])