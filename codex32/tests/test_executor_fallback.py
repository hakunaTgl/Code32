from __future__ import annotations

import asyncio
import pytest

from app.adaptive_executor import AdaptiveExecutor
from app.bot_registry import SecureRegistry
from app.models import Bot, BotDeploymentConfig, BotRole, DeploymentType
from app.exceptions import ContainerError


class FailingEngine:
    async def create_container(self, *_args, **_kwargs):
        raise ContainerError("boom")

    async def start_container(self, *_args, **_kwargs):
        raise ContainerError("boom")

    async def stop_container(self, *_args, **_kwargs):
        return True

    async def remove_container(self, *_args, **_kwargs):
        return True


@pytest.mark.asyncio
async def test_executor_falls_back_to_local_when_container_fails(tmp_path, monkeypatch):
    # Arrange a bot whose blueprint exists
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    bot_file = bots_dir / "ok.py"
    # Produce some output and read an env var to ensure we pass environment vars.
    bot_file.write_text(
        "import os\n"
        "print('hello')\n"
        "print(os.environ.get('CODEX32_TEST_ENV', 'missing'))\n"
    )

    # Patch settings to point to tmp bots dir
    from app import config as config_module

    monkeypatch.setattr(config_module.settings, "BOTS_DIRECTORY", str(bots_dir))

    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    bot = Bot(
        id="b1",
        name="b1",
        description="",
        blueprint="ok.py",
        role=BotRole.WORKER,
        deployment_config=BotDeploymentConfig(
            deployment_type=DeploymentType.CUSTOM_CONTAINER,
            environment_vars={"CODEX32_TEST_ENV": "present"},
        ),
    )
    registry.register_bot(bot)

    exec_ = AdaptiveExecutor(registry=registry, container_engine=FailingEngine())

    # Act: should not raise; should start locally after container failure
    ok = await exec_.run_bot(bot)

    # Assert
    assert ok is True
    assert bot.id in exec_.running_processes

    # Cleanup
    await exec_.stop_bot(bot.id, reason="test")


class SlowStartEngine(FailingEngine):
    async def create_container(self, *_args, **_kwargs):
        # Return an object with .metadata.process_id and .container_id attributes used by executor
        class _C:
            container_id = "c123"

            class metadata:
                process_id = 999

        return _C()

    async def start_container(self, *_args, **_kwargs):
        # Simulate a hang that triggers wait_for timeout
        await asyncio.sleep(60)


@pytest.mark.asyncio
async def test_executor_container_start_timeout_falls_back_to_local(tmp_path, monkeypatch):
    bots_dir = tmp_path / "bots"
    bots_dir.mkdir()
    bot_file = bots_dir / "ok.py"
    bot_file.write_text("print('hello')\n")

    from app import config as config_module

    monkeypatch.setattr(config_module.settings, "BOTS_DIRECTORY", str(bots_dir))

    registry_file = tmp_path / "registry.json"
    registry = SecureRegistry(registry_file=str(registry_file))

    bot = Bot(
        id="b2",
        name="b2",
        description="",
        blueprint="ok.py",
        role=BotRole.WORKER,
        deployment_config=BotDeploymentConfig(
            deployment_type=DeploymentType.CUSTOM_CONTAINER,
        ),
    )
    registry.register_bot(bot)

    exec_ = AdaptiveExecutor(registry=registry, container_engine=SlowStartEngine())

    ok = await exec_.run_bot(bot)
    assert ok is True
    assert bot.id in exec_.running_processes
    await exec_.stop_bot(bot.id, reason="test")
