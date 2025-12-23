import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    # Importing create_app ensures we include all routers.
    from main import create_app

    app = create_app()
    return TestClient(app)


def test_guide_hello_exists(client: TestClient):
    r = client.get("/api/v1/guide/hello")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert "next" in body
    assert isinstance(body["next"], list)


def test_guide_onboarding_exists(client: TestClient):
    r = client.get("/api/v1/guide/onboarding")
    assert r.status_code == 200
    body = r.json()
    assert body.get("title")
    assert isinstance(body.get("steps"), list)


def test_guide_status_shape(client: TestClient):
    r = client.get("/api/v1/guide/status")
    assert r.status_code == 200
    body = r.json()

    assert "bots" in body
    assert "executor" in body
    assert "supervisor" in body

    assert isinstance(body["bots"].get("total"), int)
    # API uses bot_ids, not ids
    assert isinstance(body["bots"].get("bot_ids"), list)


def test_guide_recommendations_shape(client: TestClient):
    r = client.get("/api/v1/guide/recommendations")
    assert r.status_code == 200
    body = r.json()

    assert "state" in body
    assert "recommendations" in body
    assert isinstance(body["recommendations"], list)

    # Always includes a low-friction docs recommendation
    assert any(rec.get("action", {}).get("path") == "/docs" for rec in body["recommendations"])
