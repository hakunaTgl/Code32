"""Pytest configuration and shared fixtures."""
import sys
import os
from pathlib import Path

import pytest

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure Pydantic/FastAPI remain compatible with Python 3.14
import app.pydantic_patch  # noqa: F401

from app.config import Settings
from app.bot_registry import SecureRegistry
from app.adaptive_executor import AdaptiveExecutor
from app.security import SecurityManager, RBACSystem


@pytest.fixture
def test_settings():
    """Provide test settings with temporary files."""
    settings = Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        REGISTRY_FILE="/tmp/test_registry.json",
        BOTS_DIRECTORY="/tmp/test_bots",
    )

    # Create test directories
    os.makedirs(settings.BOTS_DIRECTORY, exist_ok=True)

    return settings


@pytest.fixture
def registry(test_settings):
    """Provide a test registry instance."""
    reg = SecureRegistry(registry_file=test_settings.REGISTRY_FILE)

    # Ensure a deterministic starting point for tests.
    reg._cache = {}
    reg._save()
    yield reg

    # Cleanup
    if os.path.exists(test_settings.REGISTRY_FILE):
        os.remove(test_settings.REGISTRY_FILE)


@pytest.fixture
def executor(registry):
    """Provide a test executor instance."""
    return AdaptiveExecutor(registry=registry)


@pytest.fixture
def sample_bot():
    """Provide a sample bot for testing."""
    return {
        "id": "test-bot-01",
        "name": "Test Bot",
        "description": "A test bot for unit testing",
        "blueprint": "test_bot.py",
        "role": "worker",
        "deployment_config": {
            "cpu_request": "100m",
            "cpu_limit": "500m",
            "memory_request": "128Mi",
            "memory_limit": "512Mi",
        },
    }


@pytest.fixture
def sample_bots(sample_bot):
    """Provide multiple sample bots."""
    bots = [sample_bot]

    for i in range(2, 5):
        bot = {
            "id": f"test-bot-{i:02d}",
            "name": f"Test Bot {i}",
            "description": f"Test bot {i}",
            "blueprint": f"test_bot_{i}.py",
            "role": "analyzer" if i % 2 == 0 else "worker",
        }
        bots.append(bot)

    return bots


@pytest.fixture
def security_manager():
    """Provide SecurityManager instance."""
    return SecurityManager()


@pytest.fixture
def rbac_system():
    """Provide RBACSystem instance."""
    return RBACSystem()


@pytest.fixture
def test_user_token(security_manager):
    """Generate a test JWT token."""
    return security_manager.create_access_token(
        user_id="test-user-123",
        username="testuser",
        roles=["admin", "user"]
    )


@pytest.fixture
def test_admin_token(security_manager):
    """Generate a test admin JWT token."""
    return security_manager.create_access_token(
        user_id="admin-user-123",
        username="adminuser",
        roles=["admin"]
    )


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary test files after each test."""
    yield

    # Cleanup any test files
    temp_files = [
        "/tmp/test_registry.json",
        "/tmp/test_bot.py",
    ]

    for filepath in temp_files:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add asyncio marker to async tests
        if "async" in item.keywords:
            item.add_marker(pytest.mark.asyncio)
