from __future__ import annotations

from fastapi.testclient import TestClient

from main import create_app
from app.config import settings


def test_self_capabilities_exists():
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/v1/self/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["self_healing"] is True
    assert data["self_awareness"] is True
    assert data["self_enhancement"]["mode"] == "proposal-and-approve"


def test_patch_workflow_requires_admin_key():
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/v1/self/patches")
    assert resp.status_code == 401


def test_patch_workflow_happy_path(tmp_path, monkeypatch):
    # Force patch store to temp path by monkeypatching default filename via cwd
    # We'll run in tmp_path by overriding the process working directory.
    monkeypatch.chdir(tmp_path)

    app = create_app()
    client = TestClient(app)

    headers = {"X-Admin-Api-Key": settings.ADMIN_API_KEY.get_secret_value()}

    # Propose a patch
    payload = {
        "title": "Test Patch",
        "goal": "Demonstrate proposal flow",
        "diff": "*** Begin Patch\n*** End Patch",
        "rationale": "Testing",
        "risks": ["none"],
        "tests": ["pytest -q"],
    }

    propose = client.post("/api/v1/self/patches/propose", params=payload, headers=headers)
    assert propose.status_code == 201
    proposal = propose.json()
    pid = proposal["proposal_id"]

    # Approve
    approve = client.post(f"/api/v1/self/patches/{pid}/approve", headers=headers)
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    # Apply (logical apply gate)
    apply = client.post(f"/api/v1/self/patches/{pid}/apply", headers=headers)
    assert apply.status_code == 200
    assert apply.json()["status"] == "applied"
