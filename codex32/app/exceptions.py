"""Custom exception classes for Codex-32."""


class CodexException(Exception):
    """Base exception class for Codex-32."""
    pass


class OrchestrationError(CodexException):
    """Error during bot orchestration."""
    pass


class BotError(OrchestrationError):
    """Error related to bot operations."""
    pass


class BotNotFoundError(BotError):
    """Bot not found in registry."""
    pass


class BotAlreadyExistsError(BotError):
    """Bot already exists in registry."""
    pass


class BotExecutionError(BotError):
    """Error executing bot process."""
    pass


class BotDeploymentError(BotError):
    """Error deploying bot."""
    pass


class BotTerminationError(BotError):
    """Error terminating bot."""
    pass


class RegistryError(CodexException):
    """Error related to bot registry."""
    pass


class ConfigurationError(CodexException):
    """Configuration-related error."""
    pass


class AuthenticationError(CodexException):
    """Authentication failure."""
    pass


class AuthorizationError(CodexException):
    """Authorization/permission failure."""
    pass


class ValidationError(CodexException):
    """Validation of input failed."""
    pass


class StorageError(CodexException):
    """Error with storage/persistence layer."""
    pass


class ConversationalError(CodexException):
    """Error in conversational AI component."""
    pass


class STTError(ConversationalError):
    """Speech-to-text processing error."""
    pass


class IntentParsingError(ConversationalError):
    """Error parsing user intent."""
    pass


class DatabaseError(CodexException):
    """Database operation error."""
    pass


class KubernetesError(CodexException):
    """Kubernetes-related error."""
    pass


class ContainerError(CodexException):
    """Container engine-related error."""
    pass


class ExternalServiceError(CodexException):
    """Error communicating with external service."""
    pass
