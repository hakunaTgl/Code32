"""Security, authentication, and authorization utilities.

Note: This module intentionally avoids importing Pydantic models (e.g. `app.models`)
so it can run on Python versions where Pydantic may not be compatible.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, TypedDict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import AuthenticationError, AuthorizationError
from app.utils import utcnow

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenUser(TypedDict, total=False):
    """Minimal user shape derived from JWTs.

    We keep this decoupled from any Pydantic models.
    """

    user_id: str
    username: str
    roles: List[str]


class SecurityManager:
    """Manages authentication and authorization."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Previously hashed password

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: str, username: str, roles: List[str],
                          expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User ID
            username: Username
            roles: List of user roles
            expires_delta: Token expiration time delta

        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=settings.API_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "exp": utcnow() + expires_delta,
            "iat": utcnow(),
            "type": "access",
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.API_SECRET_KEY.get_secret_value(),
            algorithm=settings.API_ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create a JWT refresh token.

        Args:
            user_id: User ID

        Returns:
            Encoded JWT token
        """
        expires_delta = timedelta(days=settings.API_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user_id,
            "exp": utcnow() + expires_delta,
            "iat": utcnow(),
            "type": "refresh",
        }

        encoded_jwt = jwt.encode(
            to_encode,
            settings.API_SECRET_KEY.get_secret_value(),
            algorithm=settings.API_ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.API_SECRET_KEY.get_secret_value(),
                algorithms=[settings.API_ALGORITHM],
            )
            return payload
        except JWTError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError(f"Invalid token: {str(e)}") from e

    @staticmethod
    def verify_token_type(token_payload: dict, expected_type: str) -> bool:
        """
        Verify token is of the expected type.

        Args:
            token_payload: Decoded token payload
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            True if token type matches

        Raises:
            AuthenticationError: If token type doesn't match
        """
        token_type = token_payload.get("type")
        if token_type != expected_type:
            raise AuthenticationError(
                f"Invalid token type: expected {expected_type}, got {token_type}"
            )
        return True


class RBACSystem:
    """Role-Based Access Control (RBAC) management."""

    # Permission definitions (in production, these would come from a database)
    PERMISSIONS = {
        "admin": [
            "bot:create",
            "bot:read",
            "bot:update",
            "bot:delete",
            "bot:deploy",
            "bot:start",
            "bot:stop",
            "bot:restart",
            "system:manage",
            "user:manage",
        ],
        "operator": [
            "bot:read",
            "bot:start",
            "bot:stop",
            "bot:restart",
            "system:monitor",
        ],
        "viewer": [
            "bot:read",
            "system:monitor",
        ],
        "user": [
            "bot:read",
        ],
    }

    @staticmethod
    def get_role_permissions(role: str) -> List[str]:
        """
        Get permissions for a role.

        Args:
            role: Role name

        Returns:
            List of permissions for the role
        """
        return RBACSystem.PERMISSIONS.get(role.lower(), [])

    @staticmethod
    def has_permission(user_roles: List[str], required_permission: str) -> bool:
        """
        Check if user has required permission.

        Args:
            user_roles: List of user roles
            required_permission: Required permission string

        Returns:
            True if user has permission, False otherwise
        """
        for role in user_roles:
            permissions = RBACSystem.get_role_permissions(role)
            if required_permission in permissions or f"{required_permission}:*" in permissions:
                return True
        return False

    @staticmethod
    def authorize(user_roles: List[str], required_permission: str) -> None:
        """
        Authorize a user for an action.

        Args:
            user_roles: List of user roles
            required_permission: Required permission string

        Raises:
            AuthorizationError: If user doesn't have required permission
        """
        if not RBACSystem.has_permission(user_roles, required_permission):
            raise AuthorizationError(
                f"User does not have permission: {required_permission}"
            )

    @staticmethod
    def authorize_resource_access(user_roles: List[str], resource_id: str,
                                 action: str) -> bool:
        """
        Authorize access to a specific resource.

        Args:
            user_roles: List of user roles
            resource_id: Resource identifier
            action: Action to perform (read, write, delete, etc.)

        Returns:
            True if authorized

        Raises:
            AuthorizationError: If not authorized
        """
        # In production, check if user owns the resource or has admin role
        permission = f"resource:{action}"

        if not RBACSystem.has_permission(user_roles, permission):
            # Allow if user has admin role
            if "admin" in user_roles:
                return True
            raise AuthorizationError(
                f"Not authorized to {action} resource {resource_id}"
            )
        return True


class APIKeyManager:
    """Manage API keys for service-to-service authentication."""

    # In production, these would be stored in a secure database
    _valid_keys = {}

    @classmethod
    def is_valid_key(cls, api_key: str) -> bool:
        """
        Validate an API key.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        # Check admin API key first
        if api_key == settings.ADMIN_API_KEY.get_secret_value():
            return True

        # In production, check against database
        return api_key in cls._valid_keys

    @classmethod
    def get_key_metadata(cls, api_key: str) -> Optional[dict]:
        """
        Get metadata for an API key.

        Args:
            api_key: API key

        Returns:
            Dictionary with key metadata or None if not found
        """
        if api_key == settings.ADMIN_API_KEY.get_secret_value():
            return {
                "service": "admin",
                "roles": ["admin"],
                "created_at": None,
            }

        return cls._valid_keys.get(api_key)


class InputValidator:
    """Validate user inputs to prevent injection attacks."""

    MAX_STRING_LENGTH = 10000
    MAX_ARRAY_LENGTH = 1000
    FORBIDDEN_PATTERNS = [
        "script>",
        "javascript:",
        "onclick=",
        "onerror=",
        "onload=",
    ]

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """
        Sanitize a string input.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string

        Raises:
            ValueError: If string violates safety rules
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")

        if len(value) > cls.MAX_STRING_LENGTH:
            raise ValueError(
                f"String exceeds maximum length of {cls.MAX_STRING_LENGTH}"
            )

        # Check for forbidden patterns
        value_lower = value.lower()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in value_lower:
                raise ValueError(f"Forbidden pattern detected: {pattern}")

        return value

    @classmethod
    def validate_bot_id(cls, bot_id: str) -> str:
        """
        Validate bot ID format.

        Args:
            bot_id: Bot ID to validate

        Returns:
            Validated bot ID

        Raises:
            ValueError: If format is invalid
        """
        if not bot_id or len(bot_id) > 64:
            raise ValueError("Invalid bot ID length")

        if not all(c.isalnum() or c in "-_" for c in bot_id):
            raise ValueError(
                "Bot ID must contain only alphanumeric characters, hyphens, and underscores"
            )

        return bot_id.lower()

    @classmethod
    def validate_port(cls, port: int) -> int:
        """
        Validate port number.

        Args:
            port: Port number to validate

        Returns:
            Validated port number

        Raises:
            ValueError: If port is invalid
        """
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError("Port must be an integer between 1 and 65535")

        return port
