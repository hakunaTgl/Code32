# Codex-32: Advanced AI Orchestration System

**Version:** 1.0.0  
**License:** MIT  
**Container Engine:** Custom Built-in (No Docker Required)

A modern, scalable, and production-ready AI bot orchestration platform built with Python and FastAPI. Codex-32 provides asynchronous processing, dependency injection, multi-layered security, conversational AI integration, and comprehensive bot lifecycle management—**with a custom containerization engine that requires no Docker installation**.

## 🎯 Key Features

- **Custom Container Engine**: Built-in containerization system with process isolation, resource limits, and filesystem sandboxing—no Docker dependency
- **Asynchronous Architecture**: Full async/await support with FastAPI and asyncio for handling hundreds of concurrent bot deployments
- **Bot Lifecycle Management**: Register, deploy, monitor, and manage AI bots with atomic operations and state persistence
- **Real-time Monitoring**: Resource usage tracking (CPU, memory), performance metrics, and self-healing capabilities
- **Conversational AI**: WebSocket-based real-time chat interface with voice input support (STT integration)
- **Self-Knowledge Capability**: Bots report their status, configuration, and performance history through Redis and PostgreSQL
- **Security-First Design**: JWT authentication, RBAC, input validation, and encrypted data at rest/transit
- **Multiple Deployment Types**: Local process, custom container, or Kubernetes pod
- **Modular Architecture**: Dependency injection pattern for loose coupling and easy testing
- **Atomic Operations**: Prevent data corruption with atomic file writes and database transactions

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Container Management](#container-management)
- [Architecture Overview](#architecture-overview)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Deployment](#-deployment)
- [Security](#security)
- [Monitoring](#monitoring)

## 🚀 Installation

### Prerequisites

- **Python:** 3.9+ (tested on Python 3.14; runtime avoids a hard dependency on Pydantic)
- **PostgreSQL:** 12+ (optional—use any compatible database)
- **Redis:** 6.0+ (optional—for caching)
- **Bash:** For running setup scripts

**That's it! No Docker, no Kubernetes, no complex setup.**

### Quick Local Setup

1. **Clone and navigate:**
   ```bash
   cd codex32
   ```

2. **Run automated setup:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   This script will:
   - Check Python version
   - Create virtual environment
   - Install all dependencies
   - Create necessary directories
   - Verify installation

3. **Configure environment:**
   ```bash
   # Edit .env with your settings
   nano .env
   ```

4. **Setup database (optional):**
   ```bash
   chmod +x setup_database.sh
   ./setup_database.sh
   ```

## 🏃 Quick Start

### Option 1: Using Make (Recommended)

```bash
# View all available commands
make help

# Setup environment
make setup

# Setup database
make db-setup

# Run application
make run

# Run tests
make test
```

### Option 2: Manual Start

```bash
# Activate virtual environment
source venv/bin/activate

# Start the API
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔐 Production configuration (secrets + safety)

Codex-32 is safe-by-default: in **production mode** it will refuse to start if
you are still using the placeholder secret values.

Key environment variables:

- `CODEX32_ENV=production` (or `prod`) — enables strict secret validation.
- `CODEX32_ALLOW_DEFAULT_SECRETS=true` — allows placeholder secrets in non-prod
  environments when `DEBUG=false`.

For a production launch:

- Set `CODEX32_ENV=production`
- Set strong `API_SECRET_KEY` and `ADMIN_API_KEY`
- Restrict `CORS_ORIGINS` to trusted origins (avoid `*`)
- Run behind TLS (reverse proxy or managed ingress)

### Option 3: External services (optional)

Codex-32 does **not** require Docker. If you want PostgreSQL and/or Redis, you can run them however you prefer (local install, managed cloud, etc.) and point Codex-32 at them via `DATABASE_URL` and `REDIS_URL`.

If you prefer, there is also a `docker-compose.yml` for spinning up **only the external services** quickly during development.

## 🐳 Container Management

Codex-32 includes a **custom container engine** with a full CLI for management.

## 🧭 AI Guide (Smart Companion)

Codex-32 includes a lightweight, local-first “guide” that helps users onboard and
suggests next actions based on current system state (registered bots, supervisor
incidents, etc.). It does **not** call external AI services.

- `GET /api/v1/guide/hello` — a friendly entrypoint
- `GET /api/v1/guide/onboarding` — quick-start checklist
- `GET /api/v1/guide/status` — distilled system signals
- `GET /api/v1/guide/recommendations` — actionable next steps

### List Containers

```bash
python -m app.container_cli list
```

Output:
```
NAME                ID           STATE      PID       CREATED              
my-bot              a1b2c3d4     running    12345     2025-12-15T10:30:00
analyzer-bot        e5f6g7h8     stopped    -         2025-12-15T10:25:00
```

### Create a Container

```bash
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/sample_bot.py \
  --memory-limit 512 \
  --cpu-limit 100.0
```

### Start/Stop Containers

```bash
# Start a container
python -m app.container_cli start my-bot

# Stop a container
python -m app.container_cli stop my-bot

# Remove a container
python -m app.container_cli remove my-bot
```

### View Container Details

```bash
# Inspect container
python -m app.container_cli inspect my-bot

# View container logs
python -m app.container_cli logs my-bot

# View container statistics
python -m app.container_cli stats my-bot
```

### Environment Variables in Containers

```bash
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/sample_bot.py \
  --env DEBUG=true \
  --env LOG_LEVEL=INFO \
  --env BOT_ROLE=worker
```

### Volume Mounts

```bash
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/sample_bot.py \
  --volumes /host/path:/container/path \
  --volumes /host/data:/app/data:ro
```

### Isolation Levels

```bash
# Minimal isolation (fastest)
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/sample_bot.py \
  --isolation minimal

# Standard isolation (recommended)
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/sample_bot.py \
  --isolation standard

# Strict isolation (most secure)
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/sample_bot.py \
  --isolation strict
```

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  (main.py + routers for /bots, /auth, /system, /chat)      │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
         ┌──────▼──────┐ ┌───▼──────┐ ┌───▼──────┐
         │  Registry   │ │ Executor │ │ Security │
         │  (state)    │ │(lifecycle)│ │ Manager  │
         └──────┬──────┘ └───┬──────┘ └───┬──────┘
                │            │            │
        ┌───────▼────────────▼────────────▼──────┐
        │     Custom Container Engine            │
        │  • Process isolation                   │
        │  • Resource limits (CPU, memory)       │
        │  • Filesystem sandboxing               │
        │  • Volume mounting                     │
        │  • Health monitoring                   │
        └───────┬────────────────────────────────┘
                │
        ┌───────┴──────────────┬──────────────┐
        │                      │              │
   ┌────▼────┐         ┌──────▼──────┐ ┌───▼──────┐
   │Containers│         │ PostgreSQL  │ │  Redis   │
   │Storage   │         │  (Optional) │ │(Optional)│
   └──────────┘         └─────────────┘ └──────────┘
```

### MVC-A Pattern

- **Model**: `Bot`, `BotDeploymentConfig`, `User` (Pydantic models)
- **View**: REST API endpoints and WebSocket handlers
- **Controller**: `AdaptiveExecutor`, `SecureRegistry`, `ContainerEngine`
- **Adaptive**: Self-healing, auto-restart, resource limits

### Data Flow

1. **Bot Registration**: User creates bot via `/api/v1/bots` → Registry stores config
2. **Deployment**: FastAPI endpoint triggers `AdaptiveExecutor.run_bot()`
3. **Execution**: Executor creates container via `ContainerEngine`
4. **Monitoring**: Executor monitors resource usage, performs healing
5. **State Sync**: Changes persisted to Registry and optional database

## ⚙️ Configuration

### Environment Variables

Key configuration through `.env`:

```bash
# Container Engine
CONTAINER_STORAGE_DIR=/tmp/codex32-containers
CONTAINER_ISOLATION_LEVEL=standard  # minimal|standard|strict

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secure-key
DEBUG=false

# Database (optional)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/codex32

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Security
ADMIN_API_KEY=your-admin-key
CORS_ORIGINS=*

# Resource Limits
MEMORY_THRESHOLD_MB=500
CPU_THRESHOLD_PERCENT=90.0
```

See `.env.template` for all available options.

## 📡 API Documentation

### Interactive Docs

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints (Phase 2)

```
GET    /health              Health check
GET    /                    API info
GET    /api/v1/bots        List bots
POST   /api/v1/bots        Register bot
GET    /api/v1/bots/{id}   Get bot details
POST   /api/v1/bots/{id}/start   Start bot
POST   /api/v1/bots/{id}/stop    Stop bot
WS     /ws/updates         Real-time updates
WS     /ws/command/{user}  Conversational interface
```

## 🚀 Deployment

### Local Development

```bash
make run
```

### Production Mode

```bash
make run-prod
# Runs: uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Kubernetes

This repo includes a `k8s/` directory for future expansion. If you deploy to Kubernetes today, treat it as an advanced/DIY path and validate manifests for your environment.

## 🔒 Security

### Implemented

- ✅ JWT token authentication
- ✅ Role-Based Access Control (RBAC)
- ✅ Input validation and sanitization
- ✅ Password hashing (bcrypt)
- ✅ Process isolation via containers
- ✅ Resource limit enforcement
- ✅ Structured logging with rotation

### Best Practices

1. **Change API keys** in production
2. **Use HTTPS** with valid certificates
3. **Enable database encryption**
4. **Rotate secrets regularly**
5. **Restrict CORS origins**
6. **Monitor logs** for suspicious activity

## 📊 Monitoring

### Metrics Available

```bash
# Container statistics
python -m app.container_cli stats my-bot

# CPU, memory, process count, etc.
```

### Logging

Logs are written to `logs/` directory:
- `app.log` - Application logs
- `app-error.log` - Error logs

```python
from app import get_logger
logger = get_logger(__name__)
logger.info("Bot started successfully")
```

## 📁 Project Structure

```
codex32/
├── app/                          # Core application
│   ├── __init__.py              # Package exports
│   ├── config.py                # Configuration with Pydantic
│   ├── models.py                # Data models (Bot, User, etc.)
│   ├── utils.py                 # Utilities (atomic ops, validation)
│   ├── bot_registry.py          # Bot state management
│   ├── adaptive_executor.py     # Bot lifecycle manager
│   ├── container_engine.py      # Custom container system ⭐
│   ├── container_cli.py         # Container CLI tool ⭐
│   ├── security.py              # Auth, RBAC, validation
│   ├── exceptions.py            # Custom exceptions
│   └── logging_config.py        # Logging setup
├── bots/                         # Bot implementations
│   └── sample_bot.py            # Example bot
├── tests/                        # Test suite
│   └── conftest.py              # Test fixtures
├── main.py                       # FastAPI entry point
├── requirements.txt              # Python dependencies
├── Makefile                      # Convenient commands
├── setup.sh                      # Automated setup
├── setup_database.sh            # Database initialization
├── .env.template                # Configuration template
├── README.md                     # This file
└── ...

⭐ = New custom container engine components
```

## 🔧 Development

### Quick local launch (reliable)

If your shell PATH doesn’t pick up the virtualenv’s `uvicorn`/`python`, use the helper scripts:

- Foreground (Ctrl+C to stop): `scripts/run_api.sh`
- Detached (keeps running; logs to `logs/uvicorn.out`): `scripts/run_api_detached.sh`
- Stop detached server: `scripts/stop_api.sh`

Once running, verify:

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/docs`

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage report
make test-coverage
```

### Code Quality

```bash
make format      # Format with black
make lint        # Lint with flake8
make type-check  # Type check with mypy
```

### Creating Custom Bots

See [GETTING_STARTED.md](GETTING_STARTED.md) for bot development guide.

## 📚 Documentation

- **[README.md](README.md)** - This file (project overview)
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Quick start guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical architecture
- **[PHASE_1_COMPLETION.md](PHASE_1_COMPLETION.md)** - Phase 1 details
- **[IMPLEMENTATION_SUMMARY.txt](IMPLEMENTATION_SUMMARY.txt)** - Visual summary

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes and add tests
3. Run tests: `make test`
4. Submit pull request

## 📝 License

MIT License - See LICENSE file for details

## 🆘 Support

- **Documentation**: See docs/ directory and markdown files
- **Issues**: GitHub issues tracker
- **Discussions**: GitHub discussions

## 🎉 What's Next?

- **Phase 2**: Expand the API/WS layer with authz, richer bot controls, and event streaming
- **Phase 3**: Conversational AI with voice input
- **Phase 4**: Kubernetes deployment manifests
- **Phase 5**: Comprehensive testing and optimization

---

**Built with** ❤️ **using Python, FastAPI, and custom containerization**
