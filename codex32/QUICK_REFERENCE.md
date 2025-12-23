# Codex-32 Quick Reference Guide

A one-page cheat sheet for common tasks.

---

## 🚀 Getting Started (First Time)

```bash
# 1. Clone the repo
git clone <repo>
cd codex32

# 2. Run configuration wizard (5 min)
make configure

# 3. Start the system
make run

# Open browser: http://localhost:8000
```

---

## 🤖 Working with Bots

### Create a New Bot
```bash
make new-bot
# Prompts you to choose template and name
# Creates bot in bots/my_bot/
```

### Test Bot Locally
```bash
cd bots/my_bot
python bot.py
# Ctrl+C to stop
```

### View Available Templates
```bash
make list-templates
```

### Create Specific Template
```bash
python scripts/init-bot.py --template worker --name my_bot
python scripts/init-bot.py --template collector --name gatherer
```

---

## 🌐 API Commands

### Register a Bot
```bash
curl -X POST http://localhost:8000/api/v1/bots/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "my_bot",
    "role": "worker",
    "blueprint": "bots/my_bot/bot.py",
    "deployment_config": {
      "cpu_request": "0.5",
      "memory_request": "256Mi"
    }
  }'
```

### List All Bots
```bash
curl http://localhost:8000/api/v1/bots \
  -H "Authorization: Bearer TOKEN"
```

### Get Bot Status
```bash
curl http://localhost:8000/api/v1/bots/{bot_id} \
  -H "Authorization: Bearer TOKEN"
```

### Deploy a Bot
```bash
curl -X POST http://localhost:8000/api/v1/bots/{bot_id}/deploy \
  -H "Authorization: Bearer TOKEN"
```

### Stop a Bot
```bash
curl -X POST http://localhost:8000/api/v1/bots/{bot_id}/stop \
  -H "Authorization: Bearer TOKEN"
```

### Restart a Bot
```bash
curl -X POST http://localhost:8000/api/v1/bots/{bot_id}/restart \
  -H "Authorization: Bearer TOKEN"
```

---

## 📊 Monitoring

### View Logs
```bash
# System logs
tail -f logs/codex32.log

# Specific bot logs
tail -f logs/bots/my_bot.log

# All logs
tail -f logs/*.log
```

### Dashboard
```
http://localhost:8000/dashboard
```

### System Status
```bash
curl http://localhost:8000/api/v1/system/status
```

---

## 🔧 Development Commands

### Run Tests
```bash
# All tests
make test

# Only unit tests
make test-unit

# With coverage
make test-coverage
```

### Format Code
```bash
make format    # Black formatter
```

### Lint Code
```bash
make lint      # Flake8
```

### Type Check
```bash
make type-check  # Mypy
```

### Clean Temporary Files
```bash
make clean
```

---

## ⚙️ Configuration

### Configure (Interactive)
```bash
make configure
```

### Manual Configuration
Edit `.env` file:
```bash
nano .env
```

**Key Variables:**
```
API_HOST=127.0.0.1        # API address
API_PORT=8000             # API port
DEBUG=true                # Debug mode
DATABASE_URL=...          # Database
LOG_LEVEL=INFO            # Logging
```

---

## 🗄️ Database

### Setup Database
```bash
make db-setup
# For PostgreSQL setup
```

### Database URL Examples
```
SQLite:      sqlite:///./data/codex32.db
PostgreSQL:  postgresql://user:pass@localhost/codex32
MySQL:       mysql://user:pass@localhost/codex32
```

---

## 📁 Directory Structure

```
codex32/
├── app/                    # Main application
│   ├── config.py          # Configuration
│   ├── models.py          # Data models
│   ├── bot_registry.py    # Bot management
│   ├── adaptive_executor.py # Bot execution
│   └── routers/           # API endpoints
├── bots/                   # Your bots
│   └── my_bot/            # Individual bot
├── templates/              # Bot templates
│   ├── worker-bot/
│   ├── collector-bot/
│   └── api-bot/
├── tests/                  # Test suite
├── logs/                   # Log files
├── data/                   # Data storage
├── docs/                   # Documentation
└── scripts/                # Helper scripts
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
API_PORT=8001 make run
```

### Database Connection Failed
```bash
# Check DATABASE_URL in .env
grep DATABASE_URL .env

# Test connection
# For SQLite: just ensure ./data directory exists
# For PostgreSQL: psql -h localhost -d codex32
```

### Bot Won't Start
```bash
# Check bot file syntax
python -m py_compile bots/my_bot/bot.py

# Run bot directly to see errors
python bots/my_bot/bot.py

# Check logs
tail -f logs/bots/my_bot.log
```

### Configuration Issues
```bash
# Re-run configuration wizard
make configure

# Validate .env file
cat .env
```

---

## 📚 Documentation

| Resource | Location |
|----------|----------|
| Getting Started | `docs/getting-started.md` |
| Improvement Details | `IMPROVEMENTS_ROADMAP.md` |
| Implementation Status | `IMPLEMENTATION_CHECKLIST.md` |
| Project Summary | `PROJECT_SUMMARY.md` |
| This Guide | `QUICK_REFERENCE.md` |

---

## 🎯 Common Workflows

### Complete Setup → Bot → Deploy (15 min)
```bash
# 1. Setup
make configure        # 5 min

# 2. Create bot
make new-bot         # 2 min
cd bots/my_bot
python bot.py        # Test locally

# 3. Deploy
make run             # 3 min
# In another terminal: curl register & deploy
```

### Development Iteration
```bash
# Edit bot code
nano bots/my_bot/bot.py

# Test locally
python bots/my_bot/bot.py

# Run tests
pytest tests/

# Format code
make format

# Deploy
make run  # Auto-reloads changes
```

### Debugging
```bash
# Increase log level
LOG_LEVEL=DEBUG make run

# Watch bot logs
tail -f logs/bots/my_bot.log

# Check bot status
curl http://localhost:8000/api/v1/bots/{bot_id}

# View metrics
curl http://localhost:8000/api/v1/bots/{bot_id}/metrics
```

---

## 🔐 Security Basics

### Authentication
```bash
# Create user/token (see docs)
# Include in API calls:
-H "Authorization: Bearer YOUR_TOKEN"
```

### .env File
```bash
# Keep SECRET_KEY secret!
# Don't commit .env to git
echo ".env" >> .gitignore
```

### HTTPS (Production)
```bash
# Use reverse proxy (nginx, Traefik)
# Or use: uvicorn --ssl-keyfile --ssl-certfile
```

---

## 📈 Performance Tips

1. **Connection Pooling** - Reuse connections
2. **Batch Processing** - Process multiple items together
3. **Caching** - Enable Redis for frequently accessed data
4. **Resource Limits** - Set CPU/memory limits in config
5. **Monitoring** - Use dashboard to identify bottlenecks

---

## 🆘 Getting Help

1. **Check Logs:**
   ```bash
   tail -f logs/codex32.log
   ```

2. **Read Docs:**
   - `docs/getting-started.md` - Setup help
   - `IMPROVEMENTS_ROADMAP.md` - Feature details
   - `templates/*/README.md` - Template guides

3. **Search Issues:**
   - GitHub issues
   - Community forums

4. **Ask Questions:**
   - Create GitHub issue
   - Join community chat

---

## ⌨️ Keyboard Shortcuts

| Command | Effect |
|---------|--------|
| `Ctrl+C` | Stop current process |
| `Ctrl+D` | Exit interactive session |
| `Ctrl+L` | Clear terminal |
| `↑` | Previous command history |
| `Tab` | Auto-complete |

---

## 🌟 Pro Tips

- Use `make help` to see all available commands
- Test bots locally before deploying
- Keep `.env` file secure (add to .gitignore)
- Monitor logs regularly for errors
- Use templates as starting points
- Read docstrings in code (`python -c "import bot; help(bot)"`)
- Keep dependencies updated (`pip install -r requirements.txt --upgrade`)

---

## Version Info
- **Created:** December 2025
- **For Version:** Codex-32 1.0.0
- **Last Updated:** December 2025

---

**💡 Tip:** Bookmark this page for quick reference!

**Questions?** Check `docs/getting-started.md` or open an issue on GitHub.
