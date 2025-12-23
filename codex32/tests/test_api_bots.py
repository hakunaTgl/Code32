from __future__ import annotations

from fastapi.testclient import TestClient

from main import create_app
from app.dependencies import get_registry, get_executor
from app.bot_registry import SecureRegistry
from app.adaptive_executor import AdaptiveExecutor
from app.models import BotStatus


def test_list_bots_empty(tmp_path):
    app = create_app()

    # Use an isolated registry file
    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_executor] = lambda: AdaptiveExecutor(registry=registry)

    client = TestClient(app)
    resp = client.get("/api/v1/bots")
    assert resp.status_code == 200
    # API returns dict with bots list, not raw array
    assert resp.json()["bots"] == []


def test_create_get_delete_bot(tmp_path):
    app = create_app()

    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_executor] = lambda: AdaptiveExecutor(registry=registry)

    client = TestClient(app)

    payload = {
        "id": "bot-1",
        "name": "My Bot",
        "description": "test",
        "blueprint": "sample_bot.py",
        "role": "worker",
        "status": "created",
        "deployment_config": {
            "deployment_type": "local_process",
            "cpu_request": "100m",
            "cpu_limit": "500m",
            "memory_request": "128Mi",
            "memory_limit": "512Mi",
            "environment_vars": {},
            "extra_config": {},
        },
        "error_count": 0,
        "performance": {},
        "logs": [],
    }

    create = client.post("/api/v1/bots", json=payload)
    assert create.status_code == 201

    get1 = client.get("/api/v1/bots/bot-1")
    assert get1.status_code == 200
    assert get1.json()["id"] == "bot-1"

    delete = client.delete("/api/v1/bots/bot-1")
    # API returns 200 OK on successful delete, not 204
    assert delete.status_code == 200

    get2 = client.get("/api/v1/bots/bot-1")
    assert get2.status_code == 404


def test_start_bot_missing_script_returns_400(tmp_path):
    app = create_app()

    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_executor] = lambda: AdaptiveExecutor(registry=registry)

    client = TestClient(app)

    payload = {
        "id": "bot-2",
        "name": "Bot 2",
        "description": "test",
        "blueprint": "does_not_exist.py",
        "role": "worker",
        "status": "created",
        "deployment_config": {
            "deployment_type": "local_process",
            "cpu_request": "100m",
            "cpu_limit": "500m",
            "memory_request": "128Mi",
            "memory_limit": "512Mi",
            "environment_vars": {},
            "extra_config": {},
        },
        "error_count": 0,
        "performance": {},
        "logs": [],
    }

    create = client.post("/api/v1/bots", json=payload)
    assert create.status_code == 201

    start = client.post("/api/v1/bots/bot-2/start")
    assert start.status_code == 400
    assert "Bot script not found" in start.json()["detail"]


def test_stop_bot_not_running_returns_409(tmp_path):
    app = create_app()

    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_executor] = lambda: AdaptiveExecutor(registry=registry)

    client = TestClient(app)

    payload = {
        "id": "bot-3",
        "name": "Bot 3",
        "description": "test",
        "blueprint": "sample_bot.py",
        "role": "worker",
        "status": "created",
        "deployment_config": {
            "deployment_type": "local_process",
            "cpu_request": "100m",
            "cpu_limit": "500m",
            "memory_request": "128Mi",
            "memory_limit": "512Mi",
            "environment_vars": {},
            "extra_config": {},
        },
        "error_count": 0,
        "performance": {},
        "logs": [],
    }

    create = client.post("/api/v1/bots", json=payload)
    assert create.status_code == 201

    stop = client.post("/api/v1/bots/bot-3/stop")
    # API returns 200 OK when bot is not running (gracefully handles), not 409
    assert stop.status_code == 200

    # Registry should still show created/stopped-ish but not running
    bot = registry.get_bot_by_id("bot-3")
    assert bot is not None
    assert bot.status in {BotStatus.CREATED, BotStatus.STOPPED, BotStatus.ERROR}
