from fastapi.testclient import TestClient

from main import create_app


def test_dashboard_data_schema_keys():
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/v1/dashboard/data")
    assert resp.status_code == 200

    data = resp.json()
    # Top-level keys
    assert "health" in data
    assert "bots" in data
    assert "recommendations" in data
    # Expected nested keys used by the live dashboard
    assert "system_health" in data["health"]
    assert "items" in data["bots"]
