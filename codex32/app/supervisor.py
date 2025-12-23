"""Self-healing supervisor for bots.

This module provides a lightweight, free (no external services) supervision loop that:
- Monitors bots in the registry
- Detects crashed/stuck processes and containers
- Attempts restart with exponential backoff
- Falls back from container -> local process when container startup fails repeatedly
- Records incidents to a file-backed log for audit and self-awareness

The supervisor is intentionally conservative: it won't restart bots that are STOPPED,
PAUSED, or explicitly disabled; and it enforces safety limits to avoid restart loops.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path
from typing import Dict, Optional, List

import psutil

from app.adaptive_executor import AdaptiveExecutor
from app.bot_registry import BotStatus, SecureRegistry
from app.config import settings
from app.container_engine import ContainerState
from app.utils import utcnow

logger = logging.getLogger(__name__)


@dataclass
class Incident:
    """A recorded supervisor incident for audit and debugging."""

    incident_id: str
    bot_id: str
    bot_name: str
    kind: str  # e.g., crashed, resource, restart, quarantined
    message: str
    created_at: str = field(default_factory=lambda: utcnow().isoformat())
    data: Dict = field(default_factory=dict)


class IncidentLog:
    """File-backed incident log (append-only)."""

    def __init__(self, path: str = "codex32_incidents.jsonl"):
        self.path = Path(path)

    def append(self, incident: Incident) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(incident), ensure_ascii=False) + "\n")

    def tail(self, limit: int = 200) -> List[dict]:
        if not self.path.exists():
            return []
        # Avoid reading the entire file: keep only the last N lines.
        try:
            limit_n = max(0, int(limit))
        except Exception:
            limit_n = 200

        if limit_n <= 0:
            return []

        with self.path.open("r", encoding="utf-8") as f:
            lines = list(deque(f, maxlen=limit_n))
        out: List[dict] = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out


@dataclass
class RestartState:
    failures: int = 0
    last_attempt_at: Optional[datetime] = None
    next_allowed_at: Optional[datetime] = None


class BotSupervisor:
    """Continuously monitors bots and applies self-healing policies."""

    def __init__(
        self,
        registry: SecureRegistry,
        executor: AdaptiveExecutor,
        incident_log: Optional[IncidentLog] = None,
        interval_sec: int = 5,
        max_failures: int = 5,
    ):
        self.registry = registry
        self.executor = executor
        self.incidents = incident_log or IncidentLog()
        self.interval_sec = max(1, interval_sec)
        self.max_failures = max(1, max_failures)

        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._restart_state: Dict[str, RestartState] = {}

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("BotSupervisor started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                self._task.cancel()
        logger.info("BotSupervisor stopped")

    def _get_restart_state(self, bot_id: str) -> RestartState:
        st = self._restart_state.get(bot_id)
        if not st:
            st = RestartState()
            self._restart_state[bot_id] = st
        return st

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.tick()
            except Exception as e:
                logger.exception(f"Supervisor tick failed: {e}")
            await asyncio.sleep(self.interval_sec)

    async def tick(self) -> None:
        bots = self.registry.get_all_bots()
        now = utcnow()

        for bot_rec in bots:
            # The registry returns BotRecord wrappers (attribute + mapping-ish).
            # Normalize immediately so the rest of the supervisor deals in dicts.
            bot = dict(bot_rec)
            # Only supervise bots that are expected to be running
            status_val = None
            try:
                status_val = bot.get("status")  # type: ignore[call-arg]
            except Exception:
                status_val = getattr(bot, "status", None)

            # Support
            # - dict status strings ("running")
            # - our BotStatus enum
            # - legacy app.models.BotStatus enum (its str() looks like "BotStatus.RUNNING")
            if hasattr(status_val, "value"):
                status_val = getattr(status_val, "value")

            if str(status_val) not in {BotStatus.RUNNING.value, BotStatus.DEPLOYING.value}:
                continue

            if not await self._is_bot_healthy(bot):
                await self._handle_unhealthy(bot, now)

    async def _is_bot_healthy(self, bot: dict) -> bool:
        # Container-managed: check via executor tracking
        bot_id = str(bot.get("id"))
        if bot_id in self.executor.running_containers:
            name = self.executor.running_containers[bot_id]
            meta = self.executor.container_engine.get_container_info(name)
            # meta.state is a ContainerState (Enum) or string depending on serialization.
            if not meta:
                return False
            try:
                return meta.state == ContainerState.RUNNING or str(meta.state) == ContainerState.RUNNING.value
            except Exception:
                return False

        # Local process: check psutil process status
        pid = bot.get("process_id")
        if not pid:
            return False
        try:
            proc = psutil.Process(pid)
            if not proc.is_running():
                return False
            if proc.status() == psutil.STATUS_ZOMBIE:
                return False
        except psutil.Error:
            return False
        return True

    async def _handle_unhealthy(self, bot: dict, now: datetime) -> None:
        bot_id = str(bot.get("id"))
        st = self._get_restart_state(bot_id)
        if st.next_allowed_at and now < st.next_allowed_at:
            return

        st.failures += 1
        st.last_attempt_at = now

        if st.failures > self.max_failures:
            bot["status"] = BotStatus.ERROR.value
            bot["last_error"] = f"Supervisor quarantined bot after {st.failures} failed heal attempts"
            bot["updated_at"] = utcnow().isoformat()
            self.registry.update_bot(bot)

            self._record(bot, "quarantined", str(bot.get("last_error")), {"failures": st.failures})
            return

        # Attempt recovery
        self._record(bot, "unhealthy", "Bot unhealthy; attempting self-heal", {"failures": st.failures})

        # Strategy:
        # 1) Try stop (best-effort)
        try:
            await self.executor.stop_bot(bot_id, reason="Supervisor self-heal")
        except Exception:
            pass

        # 2) Restart using original deployment mode
        try:
            ok = await self.executor.run_bot(bot)
            if ok:
                st.next_allowed_at = now + timedelta(seconds=min(60, 2 ** st.failures))
                self._record(
                    bot,
                    "restart",
                    "Restarted bot successfully",
                    {"mode": (bot.get("deployment_config") or {}).get("deployment_type")},
                )
                return
        except Exception as e:
            self._record(
                bot,
                "restart_failed",
                f"Restart failed: {e}",
                {"mode": (bot.get("deployment_config") or {}).get("deployment_type")},
            )

        # 3) Fallback: if container mode, switch to local_process and try again
        deployment_type = str((bot.get("deployment_config") or {}).get("deployment_type") or "").lower()
        if deployment_type in {"custom_container", "container"}:
            try:
                dc = dict(bot.get("deployment_config") or {})
                dc["deployment_type"] = "local_process"
                bot["deployment_config"] = dc
                bot["updated_at"] = utcnow().isoformat()
                self.registry.update_bot(bot)

                ok = await self.executor.run_bot(bot)
                if ok:
                    st.next_allowed_at = now + timedelta(seconds=min(60, 2 ** st.failures))
                    self._record(bot, "fallback", "Fell back to local process and restarted successfully", {})
                    return
            except Exception as e:
                self._record(bot, "fallback_failed", f"Fallback restart failed: {e}", {})

        st.next_allowed_at = now + timedelta(seconds=min(60, 2 ** st.failures))

    def _record(self, bot: dict, kind: str, message: str, data: Optional[Dict] = None) -> None:
        incident = Incident(
            incident_id=f"inc-{bot.get('id')}-{int(utcnow().timestamp())}",
            bot_id=str(bot.get("id")),
            bot_name=str(bot.get("name")),
            kind=kind,
            message=message,
            data=data or {},
        )
        try:
            self.incidents.append(incident)
        except Exception as e:
            logger.warning(f"Failed to write incident log: {e}")


# Singleton-ish supervisor instance bound to the app process
_supervisor: Optional[BotSupervisor] = None


def get_supervisor() -> Optional[BotSupervisor]:
    return _supervisor


def init_supervisor(registry: SecureRegistry, executor: AdaptiveExecutor) -> BotSupervisor:
    global _supervisor
    _supervisor = BotSupervisor(
        registry=registry,
        executor=executor,
        interval_sec=getattr(settings, "HEALTH_CHECK_INTERVAL_SEC", 10),
    )
    _supervisor.start()
    return _supervisor


async def shutdown_supervisor() -> None:
    global _supervisor
    if _supervisor:
        await _supervisor.stop()
        _supervisor = None
