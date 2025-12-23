from fastapi.testclient import TestClient

from main import create_app


def test_dashboard_page_renders():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    # Basic sanity checks to ensure we're serving HTML and key content exists.
    assert "<!DOCTYPE html>" in resp.text
    assert "Codex-32 Dashboard" in resp.text
