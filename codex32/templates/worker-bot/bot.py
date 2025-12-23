"""
Worker Bot Template for Codex-32

A simple worker bot that processes tasks sequentially.
Customize the process_task() method with your business logic.

Template Features:
- Async/await for efficient I/O
- Status tracking and metrics
- Graceful shutdown
- Configurable logging
"""

import asyncio
import logging
import sys
from typing import Dict, Any
from datetime import datetime
import json


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerBot:
    """
    Template worker bot for processing tasks.

    To use this template:
    1. Customize the process_task() method with your logic
    2. Configure task source (queue, API, database, etc.)
    3. Adjust polling interval and error handling as needed
    """

    def __init__(self, name: str = "worker_bot", version: str = "1.0"):
        """
        Initialize the worker bot.

        Args:
            name: Bot identifier
            version: Bot version
        """
        self.name = name
        self.version = version
        self.role = "worker"
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None

    def get_status(self) -> Dict[str, Any]:
        """
        Return bot status information.

        Returns:
            Dict with status details
        """
        uptime = 0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "name": self.name,
            "version": self.version,
            "role": self.role,
            "running": self.running,
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat()
        }

    async def get_next_task(self) -> Dict[str, Any] | None:
        """
        Fetch the next task to process.

        This is where you connect to your task source:
        - Redis queue
        - Database polling
        - Message broker (RabbitMQ, Kafka)
        - HTTP polling
        - File system

        Override this method to implement your task source.

        Returns:
            Task dict or None if no tasks available
        """
        # TODO: Implement your task fetching logic
        # Example: fetch from Redis queue
        # Example: poll database for pending tasks
        # Example: consume from Kafka topic

        # For now, simulate a task
        await asyncio.sleep(5)  # Simulate polling delay
        return None

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single task.

        This is the main business logic method.
        Override this with your custom processing logic.

        Args:
            task: Task data to process

        Returns:
            Processing result
        """
        logger.info(f"Processing task: {task}")

        # TODO: Implement your task processing logic here
        # Examples:
        # 1. Database operations
        # 2. API calls
        # 3. ML inference
        # 4. Data transformation
        # 5. File processing
        # 6. Complex calculations

        # Simulate processing
        await asyncio.sleep(1)

        result = {
            "status": "success",
            "task_id": task.get("id", "unknown"),
            "result": "Processed successfully",
            "processed_at": datetime.now().isoformat()
        }

        logger.debug(f"Task result: {result}")
        return result

    async def handle_error(self, task: Dict[str, Any], error: Exception) -> bool:
        """
        Handle task processing errors.

        Return True to retry, False to skip.

        Args:
            task: Failed task
            error: Exception that occurred

        Returns:
            True to retry, False to skip
        """
        logger.error(f"Error processing task {task.get('id')}: {error}")
        self.error_count += 1

        # TODO: Implement error handling strategy
        # - Retry with exponential backoff
        # - Log to error queue
        # - Alert on critical errors
        # - Skip permanent failures

        # For now, skip on error
        return False

    async def run(self):
        """
        Main bot loop.

        Continuously fetches and processes tasks.
        """
        self.running = True
        self.start_time = datetime.now()
        logger.info(f"{self.name} v{self.version} started")

        try:
            while self.running:
                try:
                    # Get next task
                    task = await self.get_next_task()

                    if task is None:
                        # No tasks available, wait before retry
                        await asyncio.sleep(5)
                        continue

                    logger.info(f"Got task: {task.get('id')}")

                    # Process task
                    try:
                        result = await self.process_task(task)
                        self.processed_count += 1
                        logger.info(f"Task completed: {task.get('id')}")

                    except Exception as e:
                        should_retry = await self.handle_error(task, e)
                        if not should_retry:
                            logger.warning(f"Skipped task {task.get('id')}")

                except asyncio.CancelledError:
                    logger.info("Bot cancelled")
                    break

                except Exception as e:
                    logger.exception(f"Unexpected error in main loop: {e}")
                    self.error_count += 1
                    await asyncio.sleep(5)  # Back off on unexpected errors

        finally:
            self.running = False
            logger.info(f"{self.name} stopped")
            logger.info(f"Summary: {self.processed_count} processed, "
                       f"{self.error_count} errors")

    async def shutdown(self):
        """
        Graceful shutdown.

        Stops processing and cleans up resources.
        """
        logger.info(f"Shutting down {self.name}")
        self.running = False
        # Allow time for current task to complete
        await asyncio.sleep(0.5)

    def print_status(self):
        """Print current status."""
        status = self.get_status()
        print("\n" + "="*50)
        print(f"Status: {status['name']}")
        print("="*50)
        for key, value in status.items():
            print(f"  {key:20s}: {value}")
        print("="*50 + "\n")


async def main():
    """
    Entry point for standalone execution.

    Run with: python bot.py
    """
    logger.info("Starting worker bot in standalone mode")

    bot = WorkerBot()

    # Handle graceful shutdown
    import signal

    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(bot.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Print status every 30 seconds
    async def status_reporter():
        while bot.running:
            await asyncio.sleep(30)
            bot.print_status()

    # Run bot with periodic status reporting
    try:
        await asyncio.gather(
            bot.run(),
            status_reporter(),
            return_exceptions=True
        )
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
        await bot.shutdown()
    finally:
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")
        sys.exit(0)
