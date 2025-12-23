from __future__ import annotations

import asyncio

import pytest

from app.bot_registry import SecureRegistry
from app.adaptive_executor import AdaptiveExecutor
from app.models import Bot, BotStatus, BotDeploymentConfig, DeploymentType
from app.supervisor import BotSupervisor, IncidentLog


@pytest.mark.asyncio
async def test_supervisor_records_incident_on_unhealthy(tmp_path):
    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    # Executor with no running processes/containers will treat RUNNING bot as unhealthy.
    executor = AdaptiveExecutor(registry=registry)

    bot = Bot(
        id="b1",
        name="Bot1",
        description="",
        blueprint="sample_bot.py",
        role="worker",
        status=BotStatus.RUNNING,
        deployment_config=BotDeploymentConfig(
            deployment_type=DeploymentType.LOCAL_PROCESS,
            cpu_request="100m",
            cpu_limit="500m",
            memory_request="128Mi",
            memory_limit="512Mi",
            environment_vars={},
            extra_config={},
        ),
        error_count=0,
        performance={},
        logs=[],
    )
    registry.register_bot(bot)

    log = IncidentLog(path=str(tmp_path / "incidents.jsonl"))
    supervisor = BotSupervisor(registry=registry, executor=executor, incident_log=log, interval_sec=1, max_failures=1)

    # Single tick should attempt repair and record at least one incident.
    await supervisor.tick()

    incidents = log.tail(limit=50)
    assert len(incidents) >= 1
    assert incidents[0]["bot_id"] == "b1"
