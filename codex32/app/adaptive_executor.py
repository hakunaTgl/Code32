"""Adaptive executor for bot lifecycle management and resource monitoring."""
import asyncio
import logging
import os
import signal
import subprocess
from typing import Any, Dict, List, Optional
from datetime import datetime

import psutil

from app.bot_registry import SecureRegistry
from app.bot_registry import BotStatus, _as_dict
from app.utils import get_timestamp, utcnow
from app.config import settings
from app.container_engine import (
    ContainerEngine, ContainerConfig, ResourceLimits,
    IsolationType, get_engine
)
from app.exceptions import BotExecutionError, ContainerError

logger = logging.getLogger(__name__)


def _status_value(v: Any) -> str:
    if isinstance(v, BotStatus):
        return v.value
    return str(v)


class AdaptiveExecutor:
    """
    Manages bot subprocess execution, resource monitoring, and self-healing.

    This executor handles:
    - Starting and stopping bot processes (local or containerized)
    - Monitoring resource usage (CPU, memory)
    - Automatic termination of resource-exhausting bots
    - Performance metrics collection
    - Process health checking and recovery
    """

    def __init__(self, registry: SecureRegistry, container_engine: Optional[ContainerEngine] = None):
        """
        Initialize the adaptive executor.

        Args:
            registry: SecureRegistry instance for bot state management
            container_engine: Optional custom ContainerEngine instance
        """
        self.registry = registry
        self.container_engine = container_engine or get_engine()
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.running_psutil: Dict[str, psutil.Process] = {}
        self.process_creation_time: Dict[str, datetime] = {}
        self.running_containers: Dict[str, str] = {}  # bot_id -> container_name

    async def run_bot(self, bot: Any) -> bool:
        """
        Start a bot process asynchronously (local or containerized).

        Args:
            bot: Bot to execute

        Returns:
            True if successful, False otherwise

        Raises:
            FileNotFoundError: If bot script not found
            subprocess.SubprocessError: If process creation fails
            ContainerError: If container creation fails
        """
        try:
            bot = _as_dict(bot)
            blueprint = bot.get("blueprint")
            if not blueprint:
                raise FileNotFoundError("Bot blueprint not set")
            script_path = blueprint if os.path.isabs(blueprint) else os.path.join(settings.BOTS_DIRECTORY, blueprint)
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Bot script not found: {script_path}")

            logger.info(
                "Starting bot: %s (ID: %s), script: %s",
                bot.get("name"),
                bot.get("id"),
                script_path,
            )

            # Update bot status to deploying
            bot["status"] = _status_value(BotStatus.DEPLOYING)
            bot["updated_at"] = utcnow().isoformat()
            self.registry.update_bot(bot)

            # Choose execution method based on deployment type
            deployment_raw = ((bot.get("deployment_config") or {}).get("deployment_type") or "local_process")
            deployment_raw = str(deployment_raw).lower()
            if deployment_raw in {"custom_container", "container"}:
                try:
                    success = await self._run_bot_in_container(bot, script_path)
                except ContainerError as e:
                    # Fail-safe fallback: if container execution fails, try local execution.
                    logger.error(
                        "Container execution failed for %s; falling back to local process: %s",
                        bot.get("id"),
                        e,
                    )
                    bot["last_error"] = f"Container failed; fallback to local: {e}"
                    bot["error_count"] = int(bot.get("error_count") or 0) + 1
                    self.registry.update_bot(bot)
                    try:
                        success = await self._run_bot_locally(bot, script_path)
                    except Exception as local_e:
                        # If both container and local fail, ensure bot is left in a sane state.
                        logger.error(
                            "Local fallback also failed for %s after container failure: %s",
                            bot.get("id"),
                            local_e,
                        )
                        bot["status"] = _status_value(BotStatus.ERROR)
                        bot["last_error"] = f"Container failed ({e}); local fallback failed ({local_e})"
                        bot["error_count"] = int(bot.get("error_count") or 0) + 1
                        bot["updated_at"] = utcnow().isoformat()
                        self.registry.update_bot(bot)
                        raise
            else:
                # Default to local process
                success = await self._run_bot_locally(bot, script_path)

            return success

        except FileNotFoundError as e:
            logger.error("Bot script error for %s: %s", bot.get("id"), e)
            bot["status"] = _status_value(BotStatus.FAILED)
            bot["last_error"] = str(e)
            bot["error_count"] = int(bot.get("error_count") or 0) + 1
            self.registry.update_bot(bot)
            raise

        except (subprocess.SubprocessError, ContainerError) as e:
            logger.error("Execution error for %s: %s", bot.get("id"), e)
            bot["status"] = _status_value(BotStatus.ERROR)
            bot["last_error"] = str(e)
            bot["error_count"] = int(bot.get("error_count") or 0) + 1
            self.registry.update_bot(bot)
            raise

        except Exception as e:
            logger.exception("Unexpected error starting bot %s: %s", bot.get("id"), e)
            bot["status"] = _status_value(BotStatus.ERROR)
            bot["last_error"] = str(e)
            bot["error_count"] = int(bot.get("error_count") or 0) + 1
            self.registry.update_bot(bot)
            raise

    async def _run_bot_locally(self, bot: Dict[str, Any], script_path: str) -> bool:
        """Start bot as a local process.

        Notes:
        - Avoid piping stdout/stderr by default to prevent deadlocks if output is large.
        - Start a new process group so we can terminate children safely.
        """
        bot_env = {**os.environ, **((bot.get("deployment_config") or {}).get("environment_vars") or {})}

        # Start the bot process asynchronously
        process = await asyncio.to_thread(
            subprocess.Popen,
            ["python3", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=bot_env,
            start_new_session=True,  # Create new process group
        )

        # Store process references
        bot_id = str(bot.get("id"))
        self.running_processes[bot_id] = process
        self.running_psutil[bot_id] = psutil.Process(process.pid)
        self.process_creation_time[bot_id] = utcnow()

        # Update bot status to running
        bot["status"] = _status_value(BotStatus.RUNNING)
        bot["process_id"] = process.pid
        bot["started_at"] = utcnow().isoformat()
        bot["updated_at"] = utcnow().isoformat()
        self.registry.update_bot(bot)

        logger.info(
            "Started bot locally: %s (ID: %s, PID: %s)",
            bot.get("name"),
            bot_id,
            process.pid,
        )
        return True

    async def _run_bot_in_container(self, bot: Dict[str, Any], script_path: str) -> bool:
        """Start bot in a custom container."""
        try:
            config = bot.get("deployment_config") or {}

            def _parse_mem_limit_mb(v: str) -> int:
                # Accept formats like "512Mi", "1Gi", "1024", "512MB".
                raw = (v or "").strip().lower()
                if not raw:
                    return 512
                digits = "".join(ch for ch in raw if ch.isdigit())
                if not digits:
                    return 512
                n = int(digits)
                if raw.endswith("gi"):
                    return n * 1024
                return n

            isolation_raw = (settings.CONTAINER_ISOLATION_LEVEL or "standard").strip().lower()
            isolation = {
                "minimal": IsolationType.MINIMAL,
                "standard": IsolationType.STANDARD,
                "strict": IsolationType.STRICT,
            }.get(isolation_raw, IsolationType.STANDARD)

            # Create container configuration
            container_config = ContainerConfig(
                name=f"bot-{bot.get('id')}",
                image=script_path,
                entrypoint="python3",
                entrypoint_args=[script_path],
                environment=config.get("environment_vars"),
                resource_limits=ResourceLimits(
                    cpu_limit_percent=100.0,
                    memory_limit_mb=_parse_mem_limit_mb(config.get("memory_limit")),
                    disk_io_limit_mbps=100.0
                ),
                isolation_level=isolation,
                labels={'bot_id': str(bot.get('id')), 'bot_name': str(bot.get('name'))},
                auto_restart=(config.get('extra_config') or {}).get('auto_restart', False)
            )

            # Create container
            container = await self.container_engine.create_container(container_config)

            # Start container
            container_name = f"bot-{bot.get('id')}"
            # Hard timeout guard: container startup should not hang forever.
            try:
                success = await asyncio.wait_for(
                    self.container_engine.start_container(container_name),
                    timeout=10,
                )
            except asyncio.TimeoutError as te:
                # Best-effort cleanup: attempt stop/remove if startup is hung.
                try:
                    await self.container_engine.stop_container(container_name)
                except Exception:
                    pass
                try:
                    await self.container_engine.remove_container(container_name)
                except Exception:
                    pass
                raise ContainerError(f"Timed out starting container for bot {bot.get('id')}: {te}")

            if success:
                # Store container reference
                self.running_containers[str(bot.get("id"))] = container_name

                # Update bot with container info
                bot["status"] = _status_value(BotStatus.RUNNING)
                bot["process_id"] = container.metadata.process_id
                bot["k8s_pod_name"] = container.container_id  # Use as identifier
                bot["started_at"] = utcnow().isoformat()
                bot["updated_at"] = utcnow().isoformat()
                self.registry.update_bot(bot)

                logger.info(
                    "Started bot in container: %s (ID: %s, Container: %s)",
                    bot.get("name"),
                    bot.get("id"),
                    container.container_id,
                )
                return True
            else:
                # Best-effort cleanup when start() returns false.
                try:
                    await self.container_engine.remove_container(container_name)
                except Exception:
                    pass
                raise ContainerError(f"Failed to start container for bot {bot.get('id')}")

        except Exception as e:
            logger.error(f"Container execution error for {bot.get('id')}: {e}")
            raise ContainerError(f"Failed to run bot in container: {e}")

    async def monitor_and_heal(self, bot_id: str) -> Optional[str]:
        """
        Monitor a running bot and perform self-healing actions.

        Checks:
        - Process still alive
        - Memory usage within limits
        - CPU usage within limits
        - Updates performance metrics

        Args:
            bot_id: Bot to monitor

        Returns:
            Reason string if bot was terminated, None if still healthy
        """
        # Support both local-process bots and container-backed bots.
        if bot_id in self.running_containers:
            try:
                name = self.running_containers[bot_id]
                metrics = self.container_engine.get_container_metrics(name)
                bot = self.registry.get_bot_by_id(bot_id)
                if not bot:
                    return "bot_not_in_registry"

                # Best-effort: record metrics to bot performance.
                perf = bot.get("performance") or {}
                logs = perf.get("logs") or []
                logs.append(
                    {
                        "cpu_load": float(metrics.get("cpu_percent", 0.0)),
                        "memory_usage_mb": float(metrics.get("memory_rss_mb", 0.0)),
                        "last_heartbeat": get_timestamp(),
                    }
                )
                perf["logs"] = logs
                bot["performance"] = perf
                self.registry.update_bot(bot)
                return None
            except Exception as e:
                logger.warning(f"Error monitoring container bot {bot_id}: {e}")
                return None

        if bot_id not in self.running_psutil:
            return None  # Bot not running

        try:
            process = self.running_psutil[bot_id]
            bot = self.registry.get_bot_by_id(bot_id)

            if not bot:
                logger.warning(f"Bot {bot_id} not in registry during monitoring")
                return "bot_not_in_registry"

            # Check if process is still alive
            if not process.is_running():
                logger.warning(f"Bot {bot_id} process no longer running")
                await self.stop_bot(bot_id, reason="Process died unexpectedly")
                return "process_terminated"

            # Collect metrics
            mem_info = process.memory_info()
            mem_rss_mb = mem_info.rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=None)

            # Update performance metrics
            uptime = (utcnow() - self.process_creation_time[bot_id]).total_seconds()
            perf = bot.get("performance") or {}
            logs = perf.get("logs") or []
            logs.append(
                {
                    "cpu_load": cpu_percent,
                    "memory_usage_mb": mem_rss_mb,
                    "uptime_seconds": uptime,
                    "last_heartbeat": get_timestamp(),
                }
            )
            perf["logs"] = logs
            bot["performance"] = perf

            # Check memory threshold
            if mem_rss_mb > settings.MEMORY_THRESHOLD_MB:
                logger.warning(
                    f"Bot {bot_id} exceeds memory threshold: "
                    f"{mem_rss_mb:.1f}MB > {settings.MEMORY_THRESHOLD_MB}MB"
                )
                await self.stop_bot(
                    bot_id,
                    reason=f"Memory threshold exceeded: {mem_rss_mb:.1f}MB"
                )
                return "memory_limit_exceeded"

            # Check CPU threshold
            if cpu_percent > settings.CPU_THRESHOLD_PERCENT:
                logger.warning(
                    f"Bot {bot_id} exceeds CPU threshold: "
                    f"{cpu_percent:.1f}% > {settings.CPU_THRESHOLD_PERCENT}%"
                )
                # Log warning but don't kill (CPU spikes are often temporary)
                bot["last_error"] = f"CPU threshold exceeded: {cpu_percent:.1f}%"

            self.registry.update_bot(bot)
            return None  # Bot is healthy

        except psutil.NoSuchProcess:
            logger.warning(f"Bot {bot_id} process no longer exists")
            await self.stop_bot(bot_id, reason="Process disappeared")
            return "process_terminated"

        except psutil.AccessDenied:
            logger.warning(f"Access denied monitoring bot {bot_id}")
            return "access_denied"

        except Exception as e:
            logger.exception(f"Error monitoring bot {bot_id}: {e}")
            return None

    async def stop_bot(self, bot_id: str, reason: str = "Manual stop") -> bool:
        """
        Stop a running bot gracefully with timeout fallback to forceful kill.

        Args:
            bot_id: Bot ID to stop
            reason: Reason for stopping

        Returns:
            True if successful, False if bot not found
        """
        # Check if it's a container or process
        container_name = self.running_containers.pop(bot_id, None)
        process = self.running_processes.pop(bot_id, None)
        self.running_psutil.pop(bot_id, None)
        self.process_creation_time.pop(bot_id, None)

        bot = self.registry.get_bot_by_id(bot_id)

        if container_name:
            # Stop container
            try:
                # Retry stop once; if container engine is under load or the container
                # is already exiting, a transient error shouldn't strand the bot.
                ok = await self.container_engine.stop_container(container_name)
                if not ok:
                    await asyncio.sleep(0.25)
                    ok = await self.container_engine.stop_container(container_name)

                # Best-effort remove to avoid leaking storage/process metadata.
                try:
                    await self.container_engine.remove_container(container_name)
                except Exception:
                    # remove is best-effort; stop is the primary contract
                    pass

                if bot:
                    bot["status"] = _status_value(BotStatus.STOPPED)
                    bot["stopped_at"] = utcnow().isoformat()
                    perf = bot.get("performance") or {}
                    logs = perf.get("logs") or []
                    logs.append(
                        {
                            "timestamp": get_timestamp(),
                            "event": reason,
                            "status": "stopped",
                        }
                    )
                    perf["logs"] = logs
                    bot["performance"] = perf
                    self.registry.update_bot(bot)
                logger.info(f"Container for bot {bot_id} stopped: {reason}")
                return bool(ok)
            except Exception as e:
                logger.error(f"Error stopping container for bot {bot_id}: {e}")
                return False

        elif not process:
            logger.warning(f"Bot {bot_id} not found in running processes or containers")
            return False

        # Stop local process
        try:
            # Graceful termination with timeout
            # Prefer killing the whole process group to avoid leaving child procs.
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception:
                process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(process.wait, timeout=5),
                    timeout=6
                )
                logger.info(f"Bot {bot_id} terminated gracefully")
            except asyncio.TimeoutError:
                # Force kill if graceful termination times out
                logger.warning(f"Forceful kill for bot {bot_id} after graceful termination timeout")
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    process.kill()
                process.wait()

            if bot:
                bot["status"] = _status_value(BotStatus.STOPPED)
                bot["stopped_at"] = utcnow().isoformat()
                perf = bot.get("performance") or {}
                logs = perf.get("logs") or []
                logs.append(
                    {
                        "timestamp": get_timestamp(),
                        "event": reason,
                        "status": "stopped",
                    }
                )
                perf["logs"] = logs
                bot["performance"] = perf
                self.registry.update_bot(bot)

            logger.info(f"Stopped bot {bot_id} (ID: {bot_id}) due to: {reason}")
            return True

        except Exception as e:
            logger.exception(f"Error stopping bot {bot_id}: {e}")
            if bot:
                bot["status"] = _status_value(BotStatus.ERROR)
                bot["last_error"] = f"Stop failed: {str(e)}"
                self.registry.update_bot(bot)
            return False

    async def restart_bot(self, bot_id: str, reason: str = "Automatic restart") -> bool:
        """
        Restart a bot (stop then start).

        Args:
            bot_id: Bot to restart
            reason: Reason for restart

        Returns:
            True if successful
        """
        bot = self.registry.get_bot_by_id(bot_id)
        if not bot:
            logger.warning(f"Cannot restart non-existent bot: {bot_id}")
            return False

        try:
            logger.info(f"Restarting bot {bot_id}: {reason}")
            await self.stop_bot(bot_id, reason=reason)
            await asyncio.sleep(1)  # Brief pause before restart
            success = await self.run_bot(bot)
            return success
        except Exception as e:
            logger.exception(f"Error restarting bot {bot_id}: {e}")
            bot["status"] = _status_value(BotStatus.ERROR)
            bot["last_error"] = f"Restart failed: {str(e)}"
            self.registry.update_bot(bot)
            return False

    async def cleanup_all_bots(self) -> int:
        """
        Stop all running bots gracefully.

        Returns:
            Number of bots stopped
        """
        # Stop both local-process bots and container bots.
        total = len(self.running_processes) + len(self.running_containers)
        logger.info(f"Cleaning up {total} running bots")

        count = 0
        for bot_id in set(list(self.running_processes.keys()) + list(self.running_containers.keys())):
            if await self.stop_bot(bot_id, reason="Application shutdown"):
                count += 1

        return count

    def get_bot_process_info(self, bot_id: str) -> Optional[Dict]:
        """
        Get detailed process information for a bot.

        Args:
            bot_id: Bot ID

        Returns:
            Dictionary with process info or None if not running
        """
        if bot_id not in self.running_psutil:
            return None

        try:
            process = self.running_psutil[bot_id]
            mem_info = process.memory_info()

            return {
                "bot_id": bot_id,
                "pid": process.pid,
                "status": process.status(),
                "cpu_percent": process.cpu_percent(interval=None),
                "memory_rss_mb": mem_info.rss / (1024 * 1024),
                "memory_vms_mb": mem_info.vms / (1024 * 1024),
                "num_threads": process.num_threads(),
                "created_timestamp": self.process_creation_time.get(bot_id),
                "uptime_seconds": (
                    utcnow() - self.process_creation_time.get(bot_id, utcnow())
                ).total_seconds() if bot_id in self.process_creation_time else 0,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            logger.warning(f"Error getting process info for {bot_id}: {e}")
            return None

    def get_all_running_bots(self) -> List[str]:
        """Get list of all currently running bot IDs."""
        return list(set(list(self.running_processes.keys()) + list(self.running_containers.keys())))

    def is_bot_running(self, bot_id: str) -> bool:
        """Check if a specific bot is running."""
        return bot_id in self.running_processes or bot_id in self.running_containers
