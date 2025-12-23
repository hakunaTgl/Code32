"""Utility functions for atomic operations, validation, and helpers."""
import os
import json
import logging
import tempfile
import hashlib
import ast
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def atomic_save_json(filename: str, data: Dict[str, Any]) -> None:
    """
    Saves JSON data atomically to prevent corruption.

    Writes to a temporary file in the same directory, then atomically
    renames it to the target location.

    Args:
        filename: Path to the target JSON file
        data: Dictionary to serialize and save

    Raises:
        IOError: If write or rename operation fails
    """
    try:
        path = os.path.dirname(filename) or "."

        # Ensure directory exists
        os.makedirs(path, exist_ok=True)

        # Create temporary file in the same directory for atomic rename
        with tempfile.NamedTemporaryFile(
            dir=path, mode="w", delete=False, encoding="utf-8", suffix=".tmp"
        ) as tmp_file:
            json.dump(data, tmp_file, indent=4)
            tmp_path = tmp_file.name

        # Sync data to disk
        with open(tmp_path, "rb") as f:
            os.fsync(f.fileno())

        # Atomically replace the target file
        os.replace(tmp_path, filename)
        logger.info(f"Atomically saved data to: {filename}")

    except Exception as e:
        logger.error(f"Failed to atomically save JSON to {filename}: {e}")
        # Clean up temporary file if it exists
        try:
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
        raise IOError(f"Atomic save failed for {filename}") from e


def load_json(filename: str) -> Dict[str, Any]:
    """
    Load JSON data from file with error handling.

    Args:
        filename: Path to the JSON file

    Returns:
        Dictionary containing parsed JSON, or empty dict if file doesn't exist
    """
    if not os.path.exists(filename):
        logger.warning(f"JSON file not found: {filename}, returning empty dict")
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {filename}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load JSON from {filename}: {e}")
        return {}


def validate_bot_script(script_path: str) -> bool:
    """
    Validates bot script existence, extension, and Python syntax.

    Args:
        script_path: Path to the Python script

    Returns:
        True if valid

    Raises:
        FileNotFoundError: If script doesn't exist
        ValueError: If file is not a .py file
        SyntaxError: If Python syntax is invalid
    """
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    if not script_path.endswith(".py"):
        raise ValueError("Invalid file type: Must be a .py file")

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Validate Python syntax without executing
        ast.parse(content)
        logger.info(f"Script validation passed: {script_path}")
        return True

    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in script {script_path}: {e}") from e


def validate_file_path(base_dir: str, user_path: str) -> str:
    """
    Validates and canonicalizes a file path to prevent directory traversal attacks.

    Args:
        base_dir: The allowed base directory
        user_path: User-provided path (potentially untrusted)

    Returns:
        Canonical absolute path if valid

    Raises:
        ValueError: If path attempts to escape base directory
    """
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()

    # Ensure target is within base directory
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Path traversal detected: {user_path}")

    return str(target)


def calculate_file_hash(filepath: str, algorithm: str = "sha256") -> str:
    """
    Calculate cryptographic hash of a file for integrity verification.

    Args:
        filepath: Path to the file
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex digest of the file hash

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_timestamp() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def utcnow() -> datetime:
    """Timezone-aware UTC now.

    Prefer this over datetime.utcnow(), which is deprecated.
    """
    return datetime.now(timezone.utc)


def format_bytes(bytes_value: float, precision: int = 2) -> str:
    """
    Format bytes into human-readable format (KB, MB, GB, etc).

    Args:
        bytes_value: Number of bytes
        precision: Decimal precision

    Returns:
        Formatted string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.{precision}f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.{precision}f} PB"


def ensure_directory(path: str) -> str:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Absolute path to the directory
    """
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def cleanup_file(filepath: str) -> bool:
    """
    Safely remove a file with error handling.

    Args:
        filepath: Path to the file

    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Cleaned up file: {filepath}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Failed to clean up file {filepath}: {e}")
        return False


class AtomicFileWriter:
    """Context manager for atomic file writing operations."""

    def __init__(self, filepath: str):
        """Initialize atomic writer for a target file."""
        self.filepath = filepath
        self.tmp_file = None
        self.tmp_path = None

    def __enter__(self):
        """Create temporary file in same directory."""
        path = os.path.dirname(self.filepath) or "."
        os.makedirs(path, exist_ok=True)

        self.tmp_file = tempfile.NamedTemporaryFile(
            dir=path, mode="w", delete=False, encoding="utf-8", suffix=".tmp"
        )
        self.tmp_path = self.tmp_file.name
        return self.tmp_file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Atomically replace target file or clean up on error."""
        self.tmp_file.close()

        if exc_type is None:
            # Success: atomically replace target
            try:
                with open(self.tmp_path, "rb") as f:
                    os.fsync(f.fileno())
                os.replace(self.tmp_path, self.filepath)
                logger.debug(f"Atomic write completed: {self.filepath}")
            except Exception as e:
                logger.error(f"Atomic write failed: {e}")
                cleanup_file(self.tmp_path)
                raise
        else:
            # Error: clean up temporary file
            cleanup_file(self.tmp_path)
            logger.warning(f"Atomic write cancelled due to exception: {exc_type}")

        return False
