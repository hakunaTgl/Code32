# Getting Started with Codex-32

Welcome to Codex-32! This guide will help you set up and deploy your first bot in minutes.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Your First Bot](#your-first-bot)
5. [Deployment](#deployment)
6. [What's Next](#whats-next)

---

## System Requirements

- **Python:** 3.9 or higher
- **Operating System:** Linux, macOS, or Windows
- **RAM:** 2GB minimum (4GB recommended)
- **Disk Space:** 500MB

**Optional:**
- PostgreSQL 12+ (if using PostgreSQL instead of SQLite)
- Redis 6.0+ (for caching/queue features)

---

## Installation

### Step 1: Clone or Download Codex-32

```bash
cd your/project/directory
git clone https://github.com/yourusername/codex32.git
cd codex32
```

### Step 2: Quick Setup

Run the automated setup:

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create necessary directories

### Alternative: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data logs logs/bots
```

---

## Configuration

### Option 1: Interactive Wizard (Recommended)

Start the interactive configuration wizard:

```bash
make configure
```

This will guide you through:
- 🔧 API settings (host, port)
- 🗄️ Database configuration
- 💾 Redis setup (optional)
- 🔐 Security settings
- 📊 Logging configuration

The wizard will create a `.env` file with all your settings.

### Option 2: Manual Configuration

Create a `.env` file in the project root:

```bash
# API Settings
APP_NAME=Codex-32
APP_VERSION=1.0.0
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true

# Database (SQLite for quick start)
DATABASE_URL=sqlite:///./data/codex32.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/codex32.log

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Container Settings
CONTAINER_STORAGE_DIR=./data/containers
```

---

## Your First Bot

### Step 1: Create a Bot from Template

Create a new worker bot:

```bash
make new-bot
# Or: python scripts/init-bot.py --template worker --name hello_world
```

This creates a new bot in `bots/hello_world/` with:
- `bot.py` - Bot implementation
- `config.yaml` - Configuration
- `requirements.txt` - Dependencies
- `tests/` - Test directory

### Step 2: Customize Your Bot

Edit `bots/hello_world/bot.py`:

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Customize this method with your logic."""
    
    # Example: Process incoming data
    input_data = task.get("data")
    
    # Your business logic here
    result = f"Processed: {input_data}"
    
    return {
        "status": "success",
        "result": result
    }
```

### Step 3: Test Locally

```bash
cd bots/hello_world
python bot.py
```

You should see:
```
2025-01-15 10:30:45 - __main__ - INFO - hello_world v1.0 started
```

Press Ctrl+C to stop.

---

## Deployment

### Step 1: Start Codex-32

```bash
make run
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Register Your Bot

In another terminal, register your bot:

```bash
curl -X POST http://localhost:8000/api/v1/bots/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "hello_world",
    "description": "My first bot",
    "role": "worker",
    "blueprint": "bots/hello_world/bot.py",
    "deployment_config": {
      "cpu_request": "0.5",
      "memory_request": "256Mi"
    }
  }'
```

Response:
```json
{
  "id": "bot_123abc",
  "name": "hello_world",
  "status": "registered"
}
```

Save the `id` - you'll need it for the next step.

### Step 3: Deploy the Bot

```bash
curl -X POST http://localhost:8000/api/v1/bots/bot_123abc/deploy \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Check Bot Status

```bash
curl http://localhost:8000/api/v1/bots/bot_123abc \
  -H "Authorization: Bearer YOUR_TOKEN"
```

You should see:
```json
{
  "id": "bot_123abc",
  "name": "hello_world",
  "status": "running",
  "uptime": 45,
  "process_id": 12345
}
```

### Step 5: Monitor Dashboard

Open your browser to access the monitoring dashboard:

```
http://localhost:8000/dashboard
```

---

## Common Tasks

### View All Running Bots

```bash
curl http://localhost:8000/api/v1/bots \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Stop a Bot

```bash
curl -X POST http://localhost:8000/api/v1/bots/bot_123abc/stop \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Bot Logs

```bash
tail -f logs/bots/hello_world.log
```

### Run Tests

```bash
# Test your bot locally
cd bots/hello_world
pytest tests/ -v

# Test Codex-32
cd /path/to/codex32
make test
```

---

## What's Next?

### 🤖 Explore Different Bot Types

```bash
# List available templates
make list-templates

# Create different types
python scripts/init-bot.py --template collector --name my_collector
python scripts/init-bot.py --template api --name my_api
python scripts/init-bot.py --template ml --name my_ml_bot
```

### 📚 Read the Documentation

- [Bot Development Guide](../guides/bot-development.md)
- [API Reference](../api-reference/bots.md)
- [Deployment Strategies](../guides/deployment.md)
- [Security Best Practices](../guides/security.md)

### 💬 Try the Chat Interface

```bash
# In Codex-32 dashboard, go to Chat tab
# Or use WebSocket:
wscat -c ws://localhost:8000/api/v1/ws/chat
```

### 🔧 Advanced Features

- [Kubernetes Deployment](../guides/deployment.md#kubernetes)
- [Custom Container Engine](../guides/container-management.md)
- [Performance Tuning](../guides/performance.md)
- [Monitoring & Alerts](../guides/monitoring.md)

---

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
API_PORT=8001 make run

# Or find and kill the process
lsof -i :8000
kill -9 <PID>
```

### Database Connection Error

```bash
# Check database URL in .env
cat .env | grep DATABASE_URL

# For SQLite, ensure directory exists
mkdir -p ./data

# For PostgreSQL, verify connection
psql -h localhost -U postgres -d codex32
```

### Bot Won't Start

```bash
# Check logs
tail -f logs/codex32.log
tail -f logs/bots/your_bot.log

# Test bot locally
cd bots/your_bot
python bot.py

# Check dependencies
pip install -r requirements.txt
```

### Authentication Issues

You may need to create a user or get an API token. Check the auth endpoint:

```bash
# For quick testing, auth might be disabled in dev mode
# Check app/config.py for REQUIRE_AUTH setting
```

---

## Performance Tips

1. **Batch Operations:** Process multiple tasks together
2. **Resource Limits:** Configure CPU/memory limits in bot config
3. **Caching:** Enable Redis for frequently accessed data
4. **Monitoring:** Use dashboard to identify bottlenecks
5. **Scaling:** Deploy multiple replicas in config.yaml

---

## Getting Help

- 📖 **Documentation:** See [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)
- 🤝 **Community:** Check GitHub discussions
- 🐛 **Issues:** Report bugs on GitHub
- 💬 **Chat:** Use WebSocket chat interface in dashboard

---

## Next Steps

```bash
# 1. Configure environment
make configure

# 2. Create your first bot
make new-bot

# 3. Start Codex-32
make run

# 4. Deploy your bot
# (See Step 2 above)

# 5. Monitor in dashboard
# Open http://localhost:8000/dashboard
```

**Congratulations!** 🎉 You're ready to build amazing bots with Codex-32.

---

## Quick Reference

| Task | Command |
|------|---------|
| Configure | `make configure` |
| Start System | `make run` |
| Create Bot | `make new-bot` |
| Test Bot | `cd bots/your_bot && python bot.py` |
| View Logs | `tail -f logs/codex32.log` |
| Run Tests | `make test` |
| Check Help | `make help` |

---

**Last Updated:** December 2025  
**Version:** 1.0.0
