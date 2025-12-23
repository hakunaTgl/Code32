"""Data models for Codex-32 using Pydantic."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.utils import utcnow


class BotStatus(str, Enum):
    """Enumeration of possible bot statuses."""

    CREATED = "created"
    REGISTERED = "registered"
    DEPLOYING = "deploying"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    FAILED = "failed"
    ERROR = "error"


class BotRole(str, Enum):
    """Enumeration of bot roles/types."""

    WORKER = "worker"
    COLLECTOR = "collector"
    ANALYZER = "analyzer"
    AGGREGATOR = "aggregator"
    ORCHESTRATOR = "orchestrator"
    CUSTOM = "custom"


class DeploymentType(str, Enum):
    """Enumeration of deployment types."""

    LOCAL_PROCESS = "local_process"
    CUSTOM_CONTAINER = "custom_container"
    KUBERNETES_POD = "kubernetes_pod"


class PerformanceMetric(BaseModel):
    """Single performance metric data point."""

    timestamp: datetime
    metric_name: str
    value: float
    unit: str = ""
    labels: Dict[str, str]

    def __init__(self, **data: Any):
        data.setdefault("timestamp", utcnow())
        data.setdefault("labels", {})
        super().__init__(**data)


class BotDeploymentConfig(BaseModel):
    """Configuration for bot deployment."""

    deployment_type: DeploymentType
    image_uri: Optional[str]
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str
    replicas: int
    environment_vars: Dict[str, str]
    volumes: Dict[str, str]
    ports: Dict[str, int]
    extra_config: Dict[str, Any]

    def __init__(self, **data: Any):
        data.setdefault("deployment_type", DeploymentType.KUBERNETES_POD)
        data.setdefault("image_uri", None)
        data.setdefault("cpu_request", "100m")
        data.setdefault("cpu_limit", "500m")
        data.setdefault("memory_request", "128Mi")
        data.setdefault("memory_limit", "512Mi")
        data.setdefault("replicas", 1)
        data.setdefault("environment_vars", {})
        data.setdefault("volumes", {})
        data.setdefault("ports", {})
        data.setdefault("extra_config", {})
        super().__init__(**data)


class Bot(BaseModel):
    """Core Bot model representing an AI bot instance."""

    # Identity & Metadata
    id: str = Field(..., description="Unique bot identifier")
    name: str = Field(..., description="Human-readable bot name")
    description: str = Field(default="", description="Bot description")
    version: str = Field(default="1.0.0", description="Bot version")
    role: BotRole = Field(default=BotRole.WORKER, description="Bot role/type")

    # Execution & Deployment
    blueprint: str = Field(..., description="Path to bot blueprint/script")
    deployment_config: BotDeploymentConfig = Field(
        ..., description="Deployment configuration"
    )
    status: BotStatus = Field(default=BotStatus.REGISTERED, description="Current bot status")

    # Resource Tracking
    process_id: Optional[int]
    k8s_pod_name: Optional[str]
    k8s_deployment_name: Optional[str]

    # Performance & Monitoring
    performance: Dict[str, Any] = Field(description="Performance metrics")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    stopped_at: Optional[datetime] = Field(default=None, description="Stop timestamp")

    # Error Tracking
    last_error: Optional[str] = Field(default=None, description="Last error message")
    error_count: int = Field(default=0, description="Total error count")

    # Tags & Metadata
    tags: Dict[str, str] = Field(description="Custom tags")
    annotations: Dict[str, str] = Field(description="Annotations")

    def __init__(self, **data: Any):
        data.setdefault("description", "")
        data.setdefault("version", "1.0.0")
        data.setdefault("role", BotRole.WORKER)
        data.setdefault("deployment_config", BotDeploymentConfig())
        data.setdefault("status", BotStatus.REGISTERED)
        data.setdefault("process_id", None)
        data.setdefault("k8s_pod_name", None)
        data.setdefault("k8s_deployment_name", None)
        data.setdefault(
            "performance",
            {
                "cpu_load": 0.0,
                "memory_usage_mb": 0.0,
                "requests_per_second": 0.0,
                "error_rate": 0.0,
                "uptime_seconds": 0.0,
                "last_heartbeat": None,
                "logs": [],
            },
        )
        data.setdefault("created_at", utcnow())
        data.setdefault("updated_at", utcnow())
        data.setdefault("started_at", None)
        data.setdefault("stopped_at", None)
        data.setdefault("last_error", None)
        data.setdefault("error_count", 0)
        data.setdefault("tags", {})
        data.setdefault("annotations", {})
        super().__init__(**data)

    @validator("id")
    def validate_id(cls, v: str) -> str:
        """Validate bot ID format."""
        if not v or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Bot ID must contain only alphanumeric characters, hyphens, and underscores")
        if len(v) > 64:
            raise ValueError("Bot ID must be 64 characters or less")
        return v.lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert bot to dictionary for serialization."""
        return self.dict(exclude_none=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bot":
        """Create bot from dictionary."""
        return cls(**data)

    def update_performance(self, metrics: Dict[str, Any]) -> None:
        """Update performance metrics."""
        self.performance.update(metrics)
        self.updated_at = utcnow()

    def is_running(self) -> bool:
        """Check if bot is currently running."""
        return self.status == BotStatus.RUNNING

    def is_failed(self) -> bool:
        """Check if bot is in failed state."""
        return self.status in [BotStatus.ERROR, BotStatus.FAILED]


class BotDeploymentRecord(BaseModel):
    """Record of a bot deployment event."""

    deployment_id: str
    bot_id: str
    image_uri: str
    deployment_type: DeploymentType
    deployed_at: datetime
    terminated_at: Optional[datetime] = None
    status: BotStatus = BotStatus.DEPLOYING
    k8s_deployment_details: Dict[str, Any]
    error_message: Optional[str] = None

    def __init__(self, **data: Any):
        data.setdefault("deployment_type", DeploymentType.KUBERNETES_POD)
        data.setdefault("deployed_at", utcnow())
        data.setdefault("terminated_at", None)
        data.setdefault("status", BotStatus.DEPLOYING)
        data.setdefault("k8s_deployment_details", {})
        data.setdefault("error_message", None)
        super().__init__(**data)


class BotEndpoint(BaseModel):
    """API endpoint for a bot."""

    endpoint_id: str
    bot_id: str
    endpoint_type: str = "http"  # http, grpc, websocket, etc.
    url: str
    port: int
    status: str = "active"
    created_at: datetime
    metadata: Dict[str, Any]

    def __init__(self, **data: Any):
        data.setdefault("endpoint_type", "http")
        data.setdefault("status", "active")
        data.setdefault("created_at", utcnow())
        data.setdefault("metadata", {})
        super().__init__(**data)


class User(BaseModel):
    """User model for authentication & authorization."""

    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_active: bool
    created_at: datetime

    def __init__(self, **data: Any):
        data.setdefault("roles", [])
        data.setdefault("permissions", [])
        data.setdefault("is_active", True)
        data.setdefault("created_at", utcnow())
        super().__init__(**data)


class AuthToken(BaseModel):
    """Authentication token response."""

    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: int  # seconds

    def __init__(self, **data: Any):
        data.setdefault("refresh_token", None)
        data.setdefault("token_type", "bearer")
        super().__init__(**data)


class BotCommandRequest(BaseModel):
    """Request to execute a bot command."""

    bot_id: str
    command: str
    args: Dict[str, Any]
    timeout_seconds: int

    def __init__(self, **data: Any):
        data.setdefault("args", {})
        data.setdefault("timeout_seconds", 300)
        super().__init__(**data)


class BotStatusResponse(BaseModel):
    """Response containing bot status."""

    bot_id: str
    name: str
    status: BotStatus
    uptime_seconds: float
    cpu_load: float
    memory_usage_mb: float
    error_rate: float
    last_updated: datetime
    details: Optional[Dict[str, Any]] = None

    def __init__(self, **data: Any):
        data.setdefault("details", None)
        super().__init__(**data)


# API Request/Response Models
class ConversationalRequest(BaseModel):
    """Request for conversational interaction."""

    user_id: str
    message: str
    context: Dict[str, Any]
    session_id: Optional[str] = None

    def __init__(self, **data: Any):
        data.setdefault("context", {})
        data.setdefault("session_id", None)
        super().__init__(**data)


class ConversationalResponse(BaseModel):
    """Response from conversational engine."""

    session_id: str
    user_id: str
    response: str
    actions: List[Dict[str, Any]]
    context: Dict[str, Any]
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    def __init__(self, **data: Any):
        data.setdefault("actions", [])
        data.setdefault("context", {})
        data.setdefault("timestamp", utcnow())
        data.setdefault("details", None)
        super().__init__(**data)
