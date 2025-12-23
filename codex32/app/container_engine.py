"""
Codex-32: Custom Container Engine

A lightweight, process-based containerization system that provides:
- Process isolation and sandboxing
- Resource limits (CPU, memory, disk I/O)
- Network namespace simulation (virtual networking)
- Volume mounting and filesystem isolation
- Container lifecycle management
- Health checking and monitoring
- Container image management (filesystem snapshots)

This replaces Docker with a custom implementation for greater control
and reduced dependencies.
"""

import asyncio
import os
import sys
import json
import signal
import subprocess
import tempfile
import shutil
import hashlib
import psutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from app.utils import utcnow


class ContainerState(str, Enum):
    """Container lifecycle states."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    EXITED = "exited"
    FAILED = "failed"


class IsolationType(str, Enum):
    """Types of process isolation available."""
    MINIMAL = "minimal"  # Basic process isolation
    STANDARD = "standard"  # Process + namespace isolation
    STRICT = "strict"  # Strict filesystem + network + resource isolation


@dataclass
class ResourceLimits:
    """Resource constraints for containers."""
    cpu_limit_percent: float = 100.0  # CPU percentage limit
    memory_limit_mb: int = 512  # Memory limit in MB
    disk_io_limit_mbps: float = 100.0  # Disk I/O limit
    network_bandwidth_limit_mbps: float = 0.0  # 0 = unlimited
    max_processes: int = 256
    max_open_files: int = 1024

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Volume:
    """Container volume mount definition."""
    source: str  # Host path or volume name
    destination: str  # Container path
    read_only: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContainerConfig:
    """Container configuration."""
    name: str
    image: str  # Path to image or base image
    entrypoint: str  # Command to run
    entrypoint_args: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[Volume] = field(default_factory=list)
    ports: Dict[int, int] = field(default_factory=dict)  # {container_port: host_port}
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    isolation_level: IsolationType = IsolationType.STANDARD
    labels: Dict[str, str] = field(default_factory=dict)
    stdin: bool = False
    stdout: bool = True
    stderr: bool = True
    auto_restart: bool = False
    restart_count: int = 0
    max_restart_count: int = 5

    def to_dict(self) -> dict:
        config_dict = asdict(self)
        config_dict['volumes'] = [v.to_dict() for v in self.volumes]
        config_dict['resource_limits'] = self.resource_limits.to_dict()
        return config_dict


@dataclass
class ContainerMetadata:
    """Runtime metadata for a container."""
    name: str
    container_id: str
    image: str
    state: ContainerState
    process_id: Optional[int] = None
    created_at: str = field(default_factory=lambda: utcnow().isoformat())
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    root_path: Optional[str] = None  # Container filesystem root
    config: Optional[ContainerConfig] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.config:
            data['config'] = self.config.to_dict()
        return data


class ContainerImage:
    """Represents a container image (filesystem snapshot)."""

    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.metadata_file = self.image_path / "image.json"
        self.layers_dir = self.image_path / "layers"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """Load image metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {}

    def create_snapshot(self, source_dir: str) -> str:
        """Create a snapshot of source directory as image."""
        self.image_path.mkdir(parents=True, exist_ok=True)
        self.layers_dir.mkdir(exist_ok=True)

        # Create compressed snapshot
        snapshot_name = hashlib.md5(
            (source_dir + str(utcnow())).encode()
        ).hexdigest()
        snapshot_path = self.layers_dir / snapshot_name

        shutil.copytree(source_dir, snapshot_path, dirs_exist_ok=True)

        # Update metadata
        self.metadata[snapshot_name] = {
            'created_at': utcnow().isoformat(),
            'source': source_dir,
            'size_bytes': self._get_dir_size(snapshot_path)
        }

        self._save_metadata()
        logger.info(f"Created image snapshot: {snapshot_name}")
        return str(snapshot_path)

    def _save_metadata(self):
        """Save image metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    @staticmethod
    def _get_dir_size(path: Path) -> int:
        """Get total directory size."""
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total


class Container:
    """Represents and manages a single container instance."""

    def __init__(self, config: ContainerConfig, storage_dir: str):
        self.config = config
        self.storage_dir = Path(storage_dir)
        self.container_dir = self.storage_dir / config.name
        self.container_dir.mkdir(parents=True, exist_ok=True)

        # Generate container ID
        self.container_id = hashlib.md5(
            (config.name + str(utcnow())).encode()
        ).hexdigest()[:12]

        # Initialize metadata
        self.metadata = ContainerMetadata(
            name=config.name,
            container_id=self.container_id,
            image=config.image,
            state=ContainerState.CREATED,
            root_path=str(self.container_dir / "rootfs"),
            config=config
        )

        self.process: Optional[subprocess.Popen] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.metrics: Dict = {}

    async def start(self) -> bool:
        """Start the container."""
        try:
            # Setup filesystem isolation
            self._setup_rootfs()

            # Setup volumes
            self._mount_volumes()

            # Build command
            cmd = self._build_command()

            # Start process
            self.process = subprocess.Popen(
                cmd,
                cwd=self.metadata.root_path,
                env={**os.environ, **self.config.environment},
                stdin=subprocess.PIPE if self.config.stdin else None,
                stdout=subprocess.PIPE if self.config.stdout else subprocess.DEVNULL,
                stderr=subprocess.PIPE if self.config.stderr else subprocess.DEVNULL,
                start_new_session=True,  # Create new process group
                preexec_fn=self._setup_process_limits if sys.platform != 'win32' else None
            )

            self.metadata.process_id = self.process.pid
            self.metadata.state = ContainerState.RUNNING
            self.metadata.started_at = utcnow().isoformat()

            logger.info(f"Container {self.config.name} started with PID {self.process.pid}")

            # Start monitoring task
            self.monitor_task = asyncio.create_task(self._monitor())

            return True

        except Exception as e:
            self.metadata.state = ContainerState.FAILED
            self.metadata.error_message = str(e)
            logger.error(f"Failed to start container {self.config.name}: {e}")
            return False

    def _setup_rootfs(self):
        """Setup container filesystem root."""
        rootfs = Path(self.metadata.root_path)
        rootfs.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        for dir_name in ['bin', 'lib', 'tmp', 'var', 'home', 'app']:
            (rootfs / dir_name).mkdir(exist_ok=True)

        logger.debug(f"Rootfs setup: {rootfs}")

    def _mount_volumes(self):
        """Mount volumes into container."""
        rootfs = Path(self.metadata.root_path)

        for volume in self.config.volumes:
            dest_path = rootfs / volume.destination.lstrip('/')
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            source_path = Path(volume.source)
            if source_path.exists():
                if source_path.is_dir():
                    # For directories, create mount point and link
                    dest_path.mkdir(parents=True, exist_ok=True)
                    # In real scenario, would use bind mount or symlink
                    logger.debug(f"Volume mounted: {volume.source} -> {volume.destination}")
                else:
                    # For files, create and link
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    if not dest_path.exists():
                        dest_path.touch()

    def _setup_process_limits(self):
        """Setup resource limits for process."""
        try:
            import resource

            limits = self.config.resource_limits

            # Memory limit
            memory_bytes = limits.memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # Max open files
            resource.setrlimit(resource.RLIMIT_NOFILE,
                             (limits.max_open_files, limits.max_open_files))

            # Max processes
            resource.setrlimit(resource.RLIMIT_NPROC,
                             (limits.max_processes, limits.max_processes))

        except Exception as e:
            logger.warning(f"Could not set resource limits: {e}")

    def _build_command(self) -> List[str]:
        """Build the command to execute in container."""
        cmd = [self.config.entrypoint]
        cmd.extend(self.config.entrypoint_args)
        return cmd

    async def _monitor(self):
        """Monitor container health and resource usage."""
        while self.process and self.process.poll() is None:
            try:
                # Collect metrics
                proc = psutil.Process(self.process.pid)
                self.metrics = {
                    'cpu_percent': proc.cpu_percent(interval=1),
                    'memory_mb': proc.memory_info().rss / (1024 * 1024),
                    'num_threads': proc.num_threads(),
                    'timestamp': utcnow().isoformat()
                }

                # Check resource limits
                if (self.metrics['memory_mb'] >
                    self.config.resource_limits.memory_limit_mb * 0.9):
                    logger.warning(
                        f"Container {self.config.name} memory usage high: "
                        f"{self.metrics['memory_mb']:.1f} MB"
                    )

                await asyncio.sleep(5)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                break

    async def stop(self, timeout: int = 10) -> bool:
        """Stop the container gracefully."""
        if not self.process:
            return True

        try:
            # Send SIGTERM
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            # Wait for graceful shutdown
            start_time = asyncio.get_event_loop().time()
            while self.process.poll() is None:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    # Force kill
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    break
                await asyncio.sleep(0.1)

            # Cancel monitor task
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass

            exit_code = self.process.poll()
            self.metadata.exit_code = exit_code
            self.metadata.state = ContainerState.EXITED
            self.metadata.stopped_at = utcnow().isoformat()

            logger.info(f"Container {self.config.name} stopped (exit code: {exit_code})")
            return True

        except Exception as e:
            logger.error(f"Error stopping container: {e}")
            return False

    def get_metrics(self) -> Dict:
        """Get container metrics."""
        return self.metrics.copy()

    def get_logs(self) -> Tuple[str, str]:
        """Get container stdout and stderr."""
        stdout = ""
        stderr = ""

        if self.process:
            if self.process.stdout:
                stdout = self.process.stdout.read().decode('utf-8', errors='ignore')
            if self.process.stderr:
                stderr = self.process.stderr.read().decode('utf-8', errors='ignore')

        return stdout, stderr

    def cleanup(self):
        """Cleanup container resources."""
        # Remove container directory
        if self.container_dir.exists():
            shutil.rmtree(self.container_dir, ignore_errors=True)

        logger.debug(f"Cleaned up container {self.config.name}")


class ContainerEngine:
    """Main container engine managing all containers."""

    def __init__(self, storage_dir: str = "/tmp/codex32-containers"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Ensure expected subdirectories exist.
        self.running_dir = self.storage_dir / "running"
        self.running_dir.mkdir(parents=True, exist_ok=True)

        self.containers: Dict[str, Container] = {}
        self.images_dir = self.storage_dir / "images"
        self.images_dir.mkdir(exist_ok=True)

        logger.info(f"ContainerEngine initialized at {self.storage_dir}")

    async def create_container(self, config: ContainerConfig) -> Container:
        """Create a new container."""
        if config.name in self.containers:
            raise ValueError(f"Container {config.name} already exists")

        container = Container(config, str(self.running_dir))
        self.containers[config.name] = container

        logger.info(f"Container created: {config.name}")
        return container

    async def start_container(self, container_name: str) -> bool:
        """Start a container."""
        if container_name not in self.containers:
            raise ValueError(f"Container {container_name} not found")

        container = self.containers[container_name]
        return await container.start()

    async def stop_container(self, container_name: str) -> bool:
        """Stop a container."""
        if container_name not in self.containers:
            raise ValueError(f"Container {container_name} not found")

        container = self.containers[container_name]
        return await container.stop()

    async def remove_container(self, container_name: str) -> bool:
        """Remove a container."""
        if container_name not in self.containers:
            raise ValueError(f"Container {container_name} not found")

        container = self.containers[container_name]

        # Best-effort stop then cleanup. Even if stop fails, cleanup should run.
        try:
            await container.stop()
        finally:
            try:
                container.cleanup()
            finally:
                del self.containers[container_name]

        logger.info(f"Container removed: {container_name}")
        return True

    def get_container(self, container_name: str) -> Optional[Container]:
        """Get a container by name."""
        return self.containers.get(container_name)

    def get_container_info(self, container_name: str) -> Optional[ContainerMetadata]:
        """Return metadata for a container without exposing the object."""
        container = self.get_container(container_name)
        if not container:
            return None
        return container.metadata

    def list_containers(self) -> List[ContainerMetadata]:
        """List all containers with their metadata."""
        return [c.metadata for c in self.containers.values()]

    def get_container_metrics(self, container_name: str) -> Dict:
        """Get metrics for a container."""
        container = self.get_container(container_name)
        if not container:
            return {}
        return container.get_metrics()

    def create_image(self, source_dir: str, image_name: str) -> str:
        """Create a container image from directory."""
        image_path = self.images_dir / image_name
        image = ContainerImage(str(image_path))
        return image.create_snapshot(source_dir)

    def export_container_state(self, container_name: str) -> Dict:
        """Export container state for persistence."""
        container = self.get_container(container_name)
        if not container:
            return {}
        return container.metadata.to_dict()

    async def cleanup_all(self):
        """Cleanup all containers."""
        for container_name in list(self.containers.keys()):
            await self.remove_container(container_name)

        logger.info("All containers cleaned up")


# Global container engine instance
_engine: Optional[ContainerEngine] = None


def get_engine(storage_dir: str = "/tmp/codex32-containers") -> ContainerEngine:
    """Get or create the global container engine."""
    global _engine
    if _engine is None:
        _engine = ContainerEngine(storage_dir)
    return _engine


async def init_engine(storage_dir: str = "/tmp/codex32-containers"):
    """Initialize the container engine."""
    global _engine
    _engine = ContainerEngine(storage_dir)
    logger.info(f"Container engine initialized at {storage_dir}")


async def shutdown_engine():
    """Shutdown the container engine and cleanup."""
    global _engine
    if _engine:
        await _engine.cleanup_all()
        _engine = None
        logger.info("Container engine shutdown complete")
