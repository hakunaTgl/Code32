"""
Codex-32: Container CLI

Command-line interface for managing containers without Docker.
Provides commands for: create, start, stop, list, inspect, logs, stats, and more.

Usage:
    python -m app.container_cli create --name my-bot --image ./bots/sample_bot.py
    python -m app.container_cli start my-bot
    python -m app.container_cli list
    python -m app.container_cli inspect my-bot
"""

import asyncio
import argparse
import json
import sys
from typing import Optional
from pathlib import Path

from app.container_engine import (
    ContainerEngine, ContainerConfig, ResourceLimits, Volume,
    IsolationType, get_engine
)
from app.logging_config import get_logger

logger = get_logger(__name__)


class ContainerCLI:
    """Command-line interface for container operations."""

    def __init__(self, storage_dir: str = "/tmp/codex32-containers"):
        self.engine = ContainerEngine(storage_dir)

    def create_command(self, args: argparse.Namespace) -> int:
        """Create a new container."""
        try:
            volumes = []
            if args.volumes:
                for vol_spec in args.volumes:
                    # Format: /host/path:/container/path[:ro]
                    parts = vol_spec.split(':')
                    volumes.append(Volume(
                        source=parts[0],
                        destination=parts[1],
                        read_only=len(parts) > 2 and parts[2] == 'ro'
                    ))

            env_vars = {}
            if args.env:
                for env_spec in args.env:
                    key, value = env_spec.split('=', 1)
                    env_vars[key] = value

            resource_limits = ResourceLimits(
                cpu_limit_percent=args.cpu_limit,
                memory_limit_mb=args.memory_limit,
                disk_io_limit_mbps=args.disk_io_limit
            )

            config = ContainerConfig(
                name=args.name,
                image=args.image,
                entrypoint=args.entrypoint or args.image,
                entrypoint_args=args.args or [],
                environment=env_vars,
                volumes=volumes,
                resource_limits=resource_limits,
                isolation_level=IsolationType[args.isolation.upper()],
                labels={'created_by': 'cli'},
                auto_restart=args.auto_restart
            )

            asyncio.run(self.engine.create_container(config))
            print(f"✓ Container '{args.name}' created successfully")
            return 0

        except Exception as e:
            print(f"✗ Error creating container: {e}", file=sys.stderr)
            return 1

    def start_command(self, args: argparse.Namespace) -> int:
        """Start a container."""
        try:
            result = asyncio.run(self.engine.start_container(args.name))
            if result:
                print(f"✓ Container '{args.name}' started")
                return 0
            else:
                print(f"✗ Failed to start container '{args.name}'", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"✗ Error starting container: {e}", file=sys.stderr)
            return 1

    def stop_command(self, args: argparse.Namespace) -> int:
        """Stop a container."""
        try:
            result = asyncio.run(self.engine.stop_container(args.name))
            if result:
                print(f"✓ Container '{args.name}' stopped")
                return 0
            else:
                print(f"✗ Failed to stop container '{args.name}'", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"✗ Error stopping container: {e}", file=sys.stderr)
            return 1

    def list_command(self, args: argparse.Namespace) -> int:
        """List all containers."""
        try:
            containers = self.engine.list_containers()

            if not containers:
                print("No containers found")
                return 0

            # Print table header
            print(f"{'NAME':<20} {'ID':<12} {'STATE':<10} {'PID':<8} {'CREATED':<19}")
            print("-" * 70)

            # Print containers
            for container in containers:
                print(
                    f"{container.name:<20} "
                    f"{container.container_id:<12} "
                    f"{container.state.value:<10} "
                    f"{str(container.process_id or '-'):<8} "
                    f"{container.created_at:<19}"
                )

            return 0

        except Exception as e:
            print(f"✗ Error listing containers: {e}", file=sys.stderr)
            return 1

    def inspect_command(self, args: argparse.Namespace) -> int:
        """Inspect a container."""
        try:
            container = self.engine.get_container(args.name)
            if not container:
                print(f"✗ Container '{args.name}' not found", file=sys.stderr)
                return 1

            # Print metadata
            metadata = container.metadata.to_dict()
            print(json.dumps(metadata, indent=2))

            return 0

        except Exception as e:
            print(f"✗ Error inspecting container: {e}", file=sys.stderr)
            return 1

    def logs_command(self, args: argparse.Namespace) -> int:
        """Get container logs."""
        try:
            container = self.engine.get_container(args.name)
            if not container:
                print(f"✗ Container '{args.name}' not found", file=sys.stderr)
                return 1

            stdout, stderr = container.get_logs()

            if args.stderr:
                print(stderr)
            else:
                print(stdout)

            return 0

        except Exception as e:
            print(f"✗ Error getting logs: {e}", file=sys.stderr)
            return 1

    def stats_command(self, args: argparse.Namespace) -> int:
        """Get container statistics."""
        try:
            container = self.engine.get_container(args.name)
            if not container:
                print(f"✗ Container '{args.name}' not found", file=sys.stderr)
                return 1

            metrics = container.get_metrics()
            print(json.dumps(metrics, indent=2))

            return 0

        except Exception as e:
            print(f"✗ Error getting stats: {e}", file=sys.stderr)
            return 1

    def remove_command(self, args: argparse.Namespace) -> int:
        """Remove a container."""
        try:
            result = asyncio.run(self.engine.remove_container(args.name))
            if result:
                print(f"✓ Container '{args.name}' removed")
                return 0
            else:
                print(f"✗ Failed to remove container '{args.name}'", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"✗ Error removing container: {e}", file=sys.stderr)
            return 1

    def export_command(self, args: argparse.Namespace) -> int:
        """Export container state."""
        try:
            state = self.engine.export_container_state(args.name)

            if not state:
                print(f"✗ Container '{args.name}' not found", file=sys.stderr)
                return 1

            with open(args.output, 'w') as f:
                json.dump(state, f, indent=2)

            print(f"✓ Container state exported to {args.output}")
            return 0

        except Exception as e:
            print(f"✗ Error exporting container: {e}", file=sys.stderr)
            return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Codex-32 Container CLI - Manage containers without Docker"
    )

    parser.add_argument(
        "--storage-dir",
        default="/tmp/codex32-containers",
        help="Container storage directory"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a container')
    create_parser.add_argument('--name', required=True, help='Container name')
    create_parser.add_argument('--image', required=True, help='Image path or name')
    create_parser.add_argument('--entrypoint', help='Override entrypoint')
    create_parser.add_argument('--args', nargs='*', help='Arguments to entrypoint')
    create_parser.add_argument('--env', nargs='*', help='Environment variables (KEY=VALUE)')
    create_parser.add_argument('--volumes', nargs='*', help='Volume mounts (/host:/container[:ro])')
    create_parser.add_argument('--cpu-limit', type=float, default=100.0, help='CPU limit %')
    create_parser.add_argument('--memory-limit', type=int, default=512, help='Memory limit MB')
    create_parser.add_argument('--disk-io-limit', type=float, default=100.0, help='Disk I/O limit MBPS')
    create_parser.add_argument('--isolation', choices=['minimal', 'standard', 'strict'],
                              default='standard', help='Isolation level')
    create_parser.add_argument('--auto-restart', action='store_true', help='Auto restart on exit')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a container')
    start_parser.add_argument('name', help='Container name')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a container')
    stop_parser.add_argument('name', help='Container name')

    # List command
    subparsers.add_parser('list', help='List all containers')

    # Inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect a container')
    inspect_parser.add_argument('name', help='Container name')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Get container logs')
    logs_parser.add_argument('name', help='Container name')
    logs_parser.add_argument('--stderr', action='store_true', help='Show stderr instead of stdout')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get container statistics')
    stats_parser.add_argument('name', help='Container name')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a container')
    remove_parser.add_argument('name', help='Container name')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export container state')
    export_parser.add_argument('name', help='Container name')
    export_parser.add_argument('--output', '-o', required=True, help='Output file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = ContainerCLI(storage_dir=args.storage_dir)

    # Route commands
    if args.command == 'create':
        return cli.create_command(args)
    elif args.command == 'start':
        return cli.start_command(args)
    elif args.command == 'stop':
        return cli.stop_command(args)
    elif args.command == 'list':
        return cli.list_command(args)
    elif args.command == 'inspect':
        return cli.inspect_command(args)
    elif args.command == 'logs':
        return cli.logs_command(args)
    elif args.command == 'stats':
        return cli.stats_command(args)
    elif args.command == 'remove':
        return cli.remove_command(args)
    elif args.command == 'export':
        return cli.export_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
