# Codex-32: Advanced AI Orchestration System

**Version:** 1.0.0  
**License:** MIT

A modern, scalable, and production-ready AI bot orchestration platform built with Python, FastAPI, and Kubernetes. Codex-32 provides asynchronous processing, dependency injection, multi-layered security, conversational AI integration, and comprehensive bot lifecycle management.

## 🎯 Key Features

- **Asynchronous Architecture**: Full async/await support with FastAPI and asyncio for handling hundreds of concurrent bot deployments
- **Bot Lifecycle Management**: Register, deploy, monitor, and manage AI bots with atomic operations and state persistence
- **Real-time Monitoring**: Resource usage tracking (CPU, memory), performance metrics, and self-healing capabilities
- **Conversational AI**: WebSocket-based real-time chat interface with voice input support (STT integration)
- **Self-Knowledge Capability**: Bots report their status, configuration, and performance history through Redis and PostgreSQL
- **Security-First Design**: JWT authentication, RBAC, input validation, network policies, and encrypted data at rest/transit
- **Kubernetes Native**: Full Kubernetes support with network policies, resource limits, and declarative manifests
- **Modular Architecture**: Dependency injection pattern for loose coupling and easy testing
- **Atomic Operations**: Prevent data corruption with atomic file writes and database transactions

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Security](#security)
- [Monitoring](#monitoring)
- [Contributing](#contributing)

## 🚀 Installation

### Prerequisites

- **Python:** 3.10 or higher
- **Docker:** Latest stable version
- **kubectl:** Compatible with your Kubernetes cluster
- **PostgreSQL:** 12+ for persistent storage
- **Redis:** 6.0+ for caching and self-knowledge base

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/youorg/codex32.git
   cd codex32
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

5. **Create logs directory:**
   ```bash
   mkdir -p logs
   ```

6. **Download Vosk model (if using local STT):**
   ```bash
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   unzip vosk-model-small-en-us-0.15.zip
   mv vosk-model-small-en-us-0.15 vosk_model_small
   ```

## 🏃 Quick Start

### Running Locally

1. **Start PostgreSQL and Redis:**
   ```bash
   # Using Docker Compose (create docker-compose.yml first)
   docker-compose up -d
   ```

2. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

3. **Start the API server:**
   ```bash
   # Development mode
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   
   # Production mode
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

4. **Access the API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health check: http://localhost:8000/health

### Testing the System

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_bot_registry.py -v
```

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│              FastAPI ManagementAPI (Port 8000)              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  REST Endpoints  │  WebSocket  │  Auth & RBAC      │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────────────────┘
               │
     ┌─────────┼─────────┬──────────┬──────────┐
     │         │         │          │          │
┌────▼────┐   │    ┌────▼───┐ ┌───▼────┐ ┌──▼────┐
│Dependency│   │    │  RBAC  │ │Security│ │Logging│
│Injection │   │    │ System │ │Manager │ │Config │
└──────────┘   │    └────────┘ └────────┘ └───────┘
               │
┌──────────────┴──────────────────────────────────────────────┐
│           Core Application Layer                            │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  SecureRegistry│  │AdaptiveExecutor  │Conversational│   │
│  │  (Bot State)   │  │(Lifecycle Mgmt)  │    Agent     │   │
│  └────────────────┘  └──────────────┘  └──────────────┘   │
└──────────────┬──────────────────────────────────────────────┘
               │
     ┌─────────┼─────────┬──────────────┐
     │         │         │              │
 ┌───▼──┐  ┌──▼───┐  ┌──▼────┐  ┌─────▼────┐
 │PG SQL│  │Redis │  │Vosk   │  │Kubernetes│
 │      │  │Cache │  │STT    │  │API       │
 └──────┘  └──────┘  └───────┘  └──────────┘
```

### MVC-A Pattern

- **Model:** `SecureRegistry`, `Bot`, database schemas
- **View:** FastAPI endpoints, WebSocket handlers
- **Controller:** Route handlers, business logic orchestration
- **Adaptive Layer:** `AdaptiveExecutor`, monitoring, self-healing

## ⚙️ Configuration

### Environment Variables

All configuration is managed through `.env` file. Key variables:

```ini
# API
API_SECRET_KEY=<your-secret-key>
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
ADMIN_API_KEY=<admin-key>
RATE_LIMIT_REQUESTS=100

# STT Provider
STT_PROVIDER=vosk  # or 'google', 'azure'

# Feature Flags
ENABLE_CONVERSATIONAL_AI=true
ENABLE_VOICE_INPUT=true
```

See `.env.template` for all available options.

### Pydantic Settings

Configuration is validated and type-checked via `app/config.py`:

```python
from app.config import settings

print(settings.API_PORT)  # Typed access with IDE autocomplete
```

## 📡 API Documentation

### Core Endpoints

#### Bot Management

**Create Bot:**
```bash
POST /api/v1/bots
Content-Type: application/json
Authorization: Bearer {token}

{
  "id": "analytics-bot-v1",
  "name": "Analytics Bot",
  "description": "Data analysis and reporting",
  "blueprint": "bots/analytics_bot.py",
  "role": "analyzer"
}
```

**List Bots:**
```bash
GET /api/v1/bots
Authorization: Bearer {token}
```

**Get Bot Status:**
```bash
GET /api/v1/bots/{bot_id}
Authorization: Bearer {token}
```

**Start Bot:**
```bash
POST /api/v1/bots/{bot_id}/start
Authorization: Bearer {token}
```

**Stop Bot:**
```bash
POST /api/v1/bots/{bot_id}/stop
Authorization: Bearer {token}
```

#### Authentication

**Login:**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}
```

**Refresh Token:**
```bash
POST /api/v1/auth/refresh
Authorization: Bearer {refresh_token}
```

#### Real-time Communication

**WebSocket - Conversational Interface:**
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/command/user123?token=<jwt_token>");

// Send text command
ws.send("Run bot analytics-v1");

// Send voice data (binary chunks)
const audioChunk = /* PCM 16-bit mono audio */;
ws.send(audioChunk);

// Receive response
ws.onmessage = (event) => {
    console.log("Response:", event.data);
};
```

### Response Examples

**Successful Bot Creation:**
```json
{
  "bot_id": "analytics-bot-v1",
  "name": "Analytics Bot",
  "status": "registered",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Bot Status Response:**
```json
{
  "bot_id": "analytics-bot-v1",
  "name": "Analytics Bot",
  "status": "running",
  "uptime_seconds": 3600.5,
  "cpu_load": 45.2,
  "memory_usage_mb": 256.8,
  "error_rate": 0.001,
  "last_updated": "2024-01-15T11:30:00Z"
}
```

## 📦 Deployment

### Docker Deployment

1. **Build image:**
   ```bash
   docker build -t codex32:latest .
   docker tag codex32:latest yourregistry/codex32:v1.0.0
   docker push yourregistry/codex32:v1.0.0
   ```

2. **Run container:**
   ```bash
   docker run -d \
     --name codex32 \
     -p 8000:8000 \
     -e DATABASE_URL=postgresql://user:pass@db:5432/codex32 \
     -e REDIS_URL=redis://redis:6379/0 \
     yourregistry/codex32:v1.0.0
   ```

### Kubernetes Deployment

1. **Create namespace:**
   ```bash
   kubectl create namespace codex-32
   ```

2. **Create secrets:**
   ```bash
   kubectl create secret generic codex32-secrets \
     --from-literal=DATABASE_URL=postgresql://... \
     --from-literal=REDIS_URL=redis://... \
     --from-literal=API_SECRET_KEY=... \
     -n codex-32
   ```

3. **Deploy using manifests:**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

4. **Verify deployment:**
   ```bash
   kubectl get pods -n codex-32
   kubectl get svc -n codex-32
   kubectl logs -f deployment/codex32-api -n codex-32
   ```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🔒 Security

### Authentication & Authorization

- **JWT Tokens:** Time-limited access tokens with refresh capability
- **RBAC:** Role-based access control with fine-grained permissions
  - `admin`: Full system access
  - `operator`: Bot management and monitoring
  - `viewer`: Read-only access
  - `user`: Basic access

### Input Validation

All API inputs validated against Pydantic models:

```python
from app.security import InputValidator

# Validate bot ID
bot_id = InputValidator.validate_bot_id(user_input)

# Sanitize strings
clean_string = InputValidator.sanitize_string(user_input)
```

### Data Protection

- **Encryption at Rest:** Database encryption, Redis TLS
- **Encryption in Transit:** HTTPS/TLS for all API traffic
- **Secrets Management:** Environment variables, Kubernetes secrets
- **File Integrity:** SHA-256 hashing for sensitive files

### Network Security

Kubernetes NetworkPolicies enforce zero-trust networking:

```yaml
# API can receive from ingress controller
# API can send to database and Redis only
# Bots isolated in separate namespace
```

## 📊 Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
# Returns 200 OK with system status
```

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
# Prometheus-compatible metrics
```

### Logging

Structured logs with rotation:

- **Console:** Real-time output (development)
- **File:** `logs/codex32.log` (rotation: 10MB, 5 backups)
- **Error Log:** `logs/codex32_errors.log` (errors only)

### Performance Tracking

Bot performance metrics automatically collected:

```json
{
  "bot_id": "analytics-v1",
  "cpu_load": 45.2,
  "memory_usage_mb": 256.8,
  "uptime_seconds": 3600.5,
  "requests_per_second": 120.5,
  "error_rate": 0.001,
  "last_heartbeat": "2024-01-15T11:30:00Z"
}
```

## 🧪 Testing

### Test Structure

```
tests/
├── test_bot_registry.py        # Registry operations
├── test_adaptive_executor.py    # Bot lifecycle
├── test_security.py            # Auth & RBAC
├── test_api.py                 # API endpoints
├── test_conversational.py       # Chat features
└── conftest.py                 # Fixtures
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_bot_registry.py -v

# With coverage
pytest --cov=app --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

### Example Test

```python
def test_register_bot(registry):
    bot = Bot(
        id="test-bot",
        name="Test Bot",
        blueprint="test.py"
    )
    registered = registry.register_bot(bot)
    assert registered.id == "test-bot"
    assert registry.get_bot_by_id("test-bot") is not None
```

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **API Reference:** http://localhost:8000/redoc (ReDoc)
- **Architecture:** See `docs/ARCHITECTURE.md`
- **Deployment Guide:** See `docs/DEPLOYMENT.md`
- **Security Guide:** See `docs/SECURITY.md`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues:** GitHub Issues tracker
- **Discussions:** GitHub Discussions
- **Email:** support@codex32.dev
- **Documentation:** https://codex32.dev/docs

## 🗺️ Roadmap

- [ ] Rasa integration for advanced conversational AI
- [ ] Prometheus/Grafana monitoring stack
- [ ] Multi-region deployment support
- [ ] Advanced ML-based anomaly detection
- [ ] WebUI dashboard
- [ ] Plugin system for custom extensions

---

**Made with ❤️ by the Codex Team**
