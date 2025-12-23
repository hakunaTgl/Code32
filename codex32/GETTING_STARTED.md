# Getting Started with Codex-32

A quick-start guide to get Codex-32 running in 5 minutes with the custom container engine (no Docker required).

## 📋 Prerequisites

- Python 3.9 or higher
- 2 GB RAM minimum
- Terminal/command line access
- PostgreSQL and Redis (optional but recommended)

## ⚡ 5-Minute Quick Start

### Step 1: Clone and Setup (1 min)

```bash
cd codex32
chmod +x setup.sh
./setup.sh
```

This automated script will:
- Create Python virtual environment
- Install all dependencies
- Create necessary directories
- Validate installation

### Step 2: Configure (1 min)

```bash
# Copy and edit configuration
cp .env.template .env
nano .env  # Update API keys and database URL if needed
```

**Minimum required changes:**
- `API_SECRET_KEY` - Change to something strong
- `ADMIN_API_KEY` - Change to something strong

### Step 3: Start Application (1 min)

```bash
# Using make
make run

# Or directly with Python
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Verify Installation (1 min)

Open in browser or curl:

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/

# Interactive docs
open http://localhost:8000/docs

# AI Guide (Smart Companion)

Once the API is running, the guide endpoints can help you onboard and show you
what to do next based on current state.

```bash
# Friendly hello
curl http://localhost:8000/api/v1/guide/hello

# Suggested next steps
curl http://localhost:8000/api/v1/guide/recommendations
```
```

### Step 5: Create Your First Container (1 min)

```bash
# Create a container
python -m app.container_cli create \
  --name my-first-bot \
  --image ./bots/sample_bot.py \
  --memory-limit 512

# List containers
python -m app.container_cli list

# Start the container
python -m app.container_cli start my-first-bot

# View container info
python -m app.container_cli inspect my-first-bot
```

## 🚀 Running Without Setup Script

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p logs bots /tmp/codex32-containers

# Copy env template
cp .env.template .env

# Start application
python main.py
```

## 🐳 Container Management

Codex-32 includes a built-in container CLI (no Docker required).

### Basic Commands

```bash
# List all containers
python -m app.container_cli list

# Create a container
python -m app.container_cli create --name my-bot --image ./bots/sample_bot.py

# Start a container
python -m app.container_cli start my-bot

# Stop a container
python -m app.container_cli stop my-bot

# View container details
python -m app.container_cli inspect my-bot

# View container logs
python -m app.container_cli logs my-bot

# View container stats
python -m app.container_cli stats my-bot

# Remove a container
python -m app.container_cli remove my-bot
```

### Advanced Container Creation

```bash
# With resource limits
python -m app.container_cli create \
  --name limited-bot \
  --image ./bots/sample_bot.py \
  --memory-limit 256 \
  --cpu-limit 50.0 \
  --isolation strict

# With environment variables
python -m app.container_cli create \
  --name env-bot \
  --image ./bots/sample_bot.py \
  --env DEBUG=true \
  --env LOG_LEVEL=DEBUG

# With auto-restart on failure
python -m app.container_cli create \
  --name resilient-bot \
  --image ./bots/sample_bot.py \
  --auto-restart
```

## 📦 Database Setup (Optional)

If you want to use PostgreSQL for persistence:

```bash
# Run database setup script
chmod +x setup_database.sh
./setup_database.sh

# Update .env with database URL
# DATABASE_URL=postgresql+asyncpg://codex_user:codex_password@localhost:5432/codex32
```

### Optional: start PostgreSQL + Redis with Docker Compose

Codex-32 itself does **not** require Docker, but this repo includes a `docker-compose.yml`
that can spin up PostgreSQL and Redis for local development.

## 🔧 Using Makefile

For convenient command execution:

```bash
# View all available commands
make help

# Setup environment
make setup

# Run application
make run

# Run tests
make test

# Format code
make format

# Check types
make type-check
```

## 📝 First Steps After Installation

### 1. Explore the API

Visit http://localhost:8000/docs to see all available endpoints.

### 2. Create a Bot

```python
# Using Python API directly
from app.bot_registry import SecureRegistry, BotStatus

registry = SecureRegistry("codex32_registry.json")

bot = {
  "id": "my-first-bot",
  "name": "My First Bot",
  "description": "",
  "blueprint": "sample_bot.py",
  "role": "worker",
  "status": BotStatus.CREATED.value,
  "deployment_config": {"deployment_type": "local_process"},
  "error_count": 0,
  "performance": {},
  "logs": [],
}

registry.register_bot(bot)
print(f"Bot registered: {bot['name']}")
```

### 3. Run a Bot

```python
from app.adaptive_executor import AdaptiveExecutor

executor = AdaptiveExecutor(registry)
success = await executor.run_bot(bot)
if success:
  print(f"Bot {bot['name']} is running!")
```

### 4. Monitor Bot

```python
# Check if running
is_running = executor.is_bot_running(bot.id)

# Get process info
info = executor.get_bot_process_info(bot.id)
print(f"CPU: {info.get('cpu_percent')}%")
print(f"Memory: {info.get('memory_mb')} MB")

# Perform monitoring
reason = await executor.monitor_and_heal(bot.id)
if reason:
    print(f"Bot needed healing: {reason}")
```

## 🤖 Creating Custom Bots

### Basic Bot Structure

Create `bots/my_bot.py`:

```python
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MyBot:
    def __init__(self, bot_id):
        self.bot_id = bot_id
        self.running = True
        self.tasks_completed = 0

    async def do_work(self):
        """Main bot work loop."""
        while self.running:
            await self.process_task()
            await asyncio.sleep(10)

    async def process_task(self):
        """Process a single task."""
        try:
            # Your custom logic here
            logger.info(f"Processing task {self.tasks_completed}")
            self.tasks_completed += 1
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Task error: {e}")

    async def run(self):
        """Main entry point."""
        logger.info(f"Bot {self.bot_id} starting")
        try:
            await self.do_work()
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as e:
            logger.exception(f"Bot error: {e}")

async def main():
    bot = MyBot("my-custom-bot")
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Register and Run

```bash
# Create container
python -m app.container_cli create \
  --name my-bot \
  --image ./bots/my_bot.py

# Start it
python -m app.container_cli start my-bot

# Monitor it
python -m app.container_cli stats my-bot
```

## 🐛 Troubleshooting

### "Container storage directory not found"

```bash
mkdir -p /tmp/codex32-containers
```

### "PostgreSQL connection refused"

```bash
# Check if PostgreSQL is running
psql --version

# Start PostgreSQL (macOS)
brew services start postgresql

# Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Or use SQLite instead (no setup needed)
# Change DATABASE_URL in .env
```

### "Port 8000 already in use"

```bash
# Use different port
python main.py --port 8001

# Or kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### "ModuleNotFoundError" after installation

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "Permission denied" on setup.sh

```bash
chmod +x setup.sh
./setup.sh
```

## 📚 Example: Complete Workflow

```bash
# 1. Setup
./setup.sh

# 2. Configure
cp .env.template .env
# Edit .env...

# 3. Start app
python main.py &

# 4. Create bot container
python -m app.container_cli create \
  --name demo-bot \
  --image ./bots/sample_bot.py \
  --memory-limit 512 \
  --cpu-limit 100.0

# 5. Start bot
python -m app.container_cli start demo-bot

# 6. Monitor
python -m app.container_cli stats demo-bot

# 7. View logs
python -m app.container_cli logs demo-bot

# 8. Stop when done
python -m app.container_cli stop demo-bot

# 9. Clean up
python -m app.container_cli remove demo-bot
```

## 🔐 Security Reminders

Before running in production:

- [ ] Change `API_SECRET_KEY` in .env
- [ ] Change `ADMIN_API_KEY` in .env
- [ ] Set `DEBUG=false` in .env
- [ ] Use HTTPS (enable TLS)
- [ ] Restrict `CORS_ORIGINS` to specific domains
- [ ] Use strong database password
- [ ] Enable database encryption
- [ ] Rotate secrets regularly
- [ ] Monitor logs for suspicious activity

## 📖 Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Explore the API**: http://localhost:8000/docs
3. **Create custom bots**: See "Creating Custom Bots" above
4. **Run tests**: `make test`
5. **Check the code**: Explore `app/` directory structure

## 🆘 Common Issues

### Issue: Bots not starting

**Solution:**
1. Check if bot script exists: `ls bots/`
2. Check logs: `tail -f logs/app.log`
3. Verify container created: `python -m app.container_cli list`

### Issue: High memory usage

**Solution:**
1. Set memory limits: `--memory-limit 256`
2. Monitor bot: `python -m app.container_cli stats <bot-name>`
3. Check if leak: `kill -9 <pid>` and restart

### Issue: Database won't connect

**Solution:**
1. Verify DATABASE_URL in .env
2. Test connection: `psql -U codex_user -d codex32`
3. Run setup again: `./setup_database.sh`
4. Use in-memory mode temporarily (no database needed)

## 💡 Tips & Tricks

### Running Multiple Bots

```bash
# Create multiple containers
for i in {1..3}; do
  python -m app.container_cli create \
    --name bot-$i \
    --image ./bots/sample_bot.py
  python -m app.container_cli start bot-$i
done

# View all
python -m app.container_cli list
```

### Development Mode

```bash
# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# With debug logging
DEBUG=true LOG_LEVEL=DEBUG python main.py
```

### Monitoring in Real-Time

```bash
# Terminal 1: Run app
python main.py

# Terminal 2: Watch containers
watch -n 2 'python -m app.container_cli list'

# Terminal 3: Monitor specific bot
watch -n 2 'python -m app.container_cli stats my-bot'
```

## 🎉 You're All Set!

Codex-32 is now running with the custom container engine. Start building amazing AI orchestration workflows!

For more information:
- 📖 [README.md](README.md) - Full documentation
- 🏗️ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture details
- 💾 [IMPLEMENTATION_SUMMARY.txt](IMPLEMENTATION_SUMMARY.txt) - What was built

---

**Happy coding!** 🚀

## Quick Start (5 minutes)

### Option 1: Docker Compose (Recommended for Development)

```bash
# 1. Clone repository
git clone https://github.com/youorg/codex32.git
cd codex32

# 2. Create environment file
cp .env.template .env

# 3. Start all services
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# 5. Check API health
curl http://localhost:8000/health

# 6. Access Swagger UI
open http://localhost:8000/docs
```

**Services will be available at:**
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Option 2: Local Installation

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download Vosk model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk_model_small

# 4. Set up environment
cp .env.template .env
# Edit .env with local PostgreSQL/Redis settings

# 5. Initialize database
# psql -U postgres -f init_db.sql  # Run database setup script

# 6. Run application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## First Steps

### 1. Access the API Documentation

Open your browser and navigate to:
```
http://localhost:8000/docs
```

This opens Swagger UI with interactive API exploration.

### 2. Register a Bot

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/bots" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "id": "analytics-bot-01",
    "name": "Analytics Bot",
    "description": "Performs data analysis",
    "blueprint": "bots/sample_bot.py",
    "role": "analyzer"
  }'
```

**Using Swagger UI:**
1. Navigate to `/docs`
2. Find the "POST /api/v1/bots" endpoint
3. Click "Try it out"
4. Enter bot details in the request body
5. Click "Execute"

### 3. Start a Bot

```bash
curl -X POST "http://localhost:8000/api/v1/bots/analytics-bot-01/start" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Monitor Bot Status

```bash
curl "http://localhost:8000/api/v1/bots/analytics-bot-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response example:
```json
{
  "bot_id": "analytics-bot-01",
  "name": "Analytics Bot",
  "status": "running",
  "uptime_seconds": 127.5,
  "cpu_load": 12.3,
  "memory_usage_mb": 256.8,
  "error_rate": 0.0,
  "last_updated": "2024-01-15T12:30:00Z"
}
```

### 5. Stop a Bot

```bash
curl -X POST "http://localhost:8000/api/v1/bots/analytics-bot-01/stop" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Creating Your Own Bot

### Bot Structure

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

class MyBot:
    def __init__(self):
        self.running = True
        logger.info("Bot initialized")
    
    async def run(self):
        """Main bot execution."""
        while self.running:
            # Do your bot work here
            await asyncio.sleep(10)
    
    def get_status(self):
        """Return bot status."""
        return {"status": "running", "tasks": 42}

async def main():
    bot = MyBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Registering Your Bot

1. Place bot script in `bots/` directory
2. Register via API:
```bash
curl -X POST "http://localhost:8000/api/v1/bots" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-bot",
    "name": "My Bot",
    "blueprint": "bots/my_bot.py"
  }'
```

## Understanding the Architecture

### Component Overview

```
┌─────────────────────────────────┐
│   FastAPI (REST + WebSocket)    │
│   Port 8000                     │
└────────────┬────────────────────┘
             │
    ┌────────┴──────────┐
    │                   │
┌───▼──────────┐   ┌───▼──────────┐
│SecureRegistry│   │AdaptiveExecutor
│(Bot State)   │   │(Lifecycle Mgmt)
└───┬──────────┘   └────┬─────────┘
    │                   │
    └────────┬──────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼──────┐  ┌──────▼───┐
│PostgreSQL│  │Redis Cache
│Database  │  │           
└──────────┘  └───────────┘
```

### Data Flow

1. **Bot Registration:** Bot metadata stored in PostgreSQL
2. **Bot Execution:** AdaptiveExecutor starts bot process
3. **Monitoring:** Metrics collected via psutil
4. **Self-Knowledge:** Status cached in Redis
5. **API Access:** Clients query via REST/WebSocket

## Configuration

### Key Environment Variables

```env
# API Settings
API_PORT=8000
API_SECRET_KEY=your-secret-key  # Change in production!

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/codex32

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring
MEMORY_THRESHOLD_MB=500      # Kill bot if exceeds
CPU_THRESHOLD_PERCENT=90.0   # Warn if exceeds

# STT (Speech-to-Text)
STT_PROVIDER=vosk            # or 'google', 'azure'
```

## Common Tasks

### View Logs

```bash
# Docker Compose
docker-compose logs -f codex32-api

# Local (with running server)
tail -f logs/codex32.log
```

### Clear Registry

```bash
# Reset all bot registrations (WARNING: destructive)
curl -X POST "http://localhost:8000/api/v1/admin/clear-registry" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Export/Import Registry

```bash
# Export backup
curl "http://localhost:8000/api/v1/admin/export-registry" \
  -H "Authorization: Bearer YOUR_TOKEN" > registry_backup.json

# Import from backup
curl -X POST "http://localhost:8000/api/v1/admin/import-registry" \
  -H "Content-Type: application/json" \
  -d @registry_backup.json
```

## Troubleshooting

### "Connection refused" on port 8000

```bash
# Check if service is running
docker-compose ps
docker-compose logs codex32-api

# Or locally
lsof -i :8000
```

### Database connection error

```bash
# Verify PostgreSQL is running
docker-compose logs postgres

# Test connection
psql -U codex_user -h localhost -d codex32
```

### Bot won't start

1. Check bot script syntax:
   ```bash
   python3 bots/your_bot.py
   ```

2. Check logs:
   ```bash
   docker-compose logs -f codex32-api
   ```

3. Verify blueprint path in registration matches actual file

### Out of memory

Increase Docker memory limit:
```bash
# Edit docker-compose.yml
services:
  codex32-api:
    mem_limit: 4g  # Increase as needed
```

## Next Steps

1. **Read the Docs:**
   - [Architecture](docs/ARCHITECTURE.md)
   - [API Reference](docs/API.md)
   - [Security Guide](docs/SECURITY.md)

2. **Deploy to Kubernetes:**
   - Follow [Kubernetes Deployment Guide](docs/DEPLOYMENT_K8S.md)

3. **Integrate Conversational AI:**
   - Setup Rasa for advanced chat
   - Configure STT providers

4. **Monitor Production:**
   - Setup Prometheus/Grafana
   - Configure alerts

## Support & Resources

- **Documentation:** https://codex32.dev/docs
- **Issues:** GitHub Issues
- **Discussion:** GitHub Discussions
- **Email:** support@codex32.dev

## Security Reminder ⚠️

Before deploying to production:

- [ ] Change `API_SECRET_KEY` to a strong random value
- [ ] Change `ADMIN_API_KEY` to a strong random value
- [ ] Use strong database password
- [ ] Enable HTTPS (TLS certificate)
- [ ] Restrict API access via firewall/network policies
- [ ] Enable rate limiting
- [ ] Review CORS settings
- [ ] Rotate secrets regularly

## What's Next?

Once you're comfortable with the basics:

1. **Create custom bots** with your business logic
2. **Configure monitoring** with Prometheus/Grafana
3. **Deploy to Kubernetes** for production
4. **Integrate Rasa** for advanced conversational AI
5. **Setup CI/CD pipeline** for automated deployments

Happy orchestrating! 🚀
