# 🎯 QUICK START - System is Live

## ✅ System Status
**Codex-32 is RUNNING** at http://localhost:8000

---

## 🚀 Get Started in 3 Steps

### Step 1: Open Dashboard
```bash
open http://localhost:8000
```
or
```
http://localhost:8000
```

### Step 2: Create Your First Bot
```bash
make new-bot
```
Follow the prompts:
- **Name:** my_first_bot
- **Template:** worker

### Step 3: Check It's Working
```bash
curl http://localhost:8000/api/v1/bots
```

---

## 📋 Essential Commands

### Running
```bash
make run        # Start system
make stop       # Stop system
```

### Bot Management
```bash
make new-bot         # Create new bot
make list-templates  # See available templates
```

### Configuration
```bash
make configure      # Set up environment
cat .env           # View current config
```

### Monitoring
```bash
tail -f logs/codex32.log  # View live logs
curl http://localhost:8000/api/v1/health  # Health check
```

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| **Dashboard** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/api/v1/health |
| **Bot Registry** | http://localhost:8000/api/v1/bots |

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [SYSTEM_LAUNCHED.md](./SYSTEM_LAUNCHED.md) | Launch details & status |
| [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) | Command reference |
| [CORRECTIONS_APPLIED.md](./CORRECTIONS_APPLIED.md) | Security fixes |
| [docs/getting-started.md](./docs/getting-started.md) | 15-min setup |
| [templates/worker-bot/README.md](./templates/worker-bot/README.md) | Bot template guide |

---

## 🎯 Common Tasks

### Register a Bot
```bash
curl -X POST http://localhost:8000/api/v1/bots/register \
  -H "Content-Type: application/json" \
  -d @bots/my_bot/config.yaml
```

### Submit a Task
```bash
curl -X POST http://localhost:8000/api/v1/bots/{bot_id}/task \
  -H "Content-Type: application/json" \
  -d '{"task": "process", "data": {}}'
```

### Check Bot Status
```bash
curl http://localhost:8000/api/v1/bots/{bot_id}/status
```

### View Logs
```bash
tail -f logs/codex32.log
grep "ERROR" logs/codex32.log
```

---

## 🔒 Security Reminders

**For Production:**
- [ ] Update API keys in `.env` (not placeholder values)
- [ ] Use `make configure` to set production secrets
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Set up monitoring

---

## ❓ Troubleshooting

**Port 8000 in use?**
```bash
pkill -f "python main.py"
make run
```

**Bot creation failing?**
```bash
# Check dependencies
pip install -r requirements.txt

# Check bot name is valid (alphanumeric, dash, underscore only)
```

**API not responding?**
```bash
# Check logs
tail -f logs/codex32.log

# Restart system
make stop
make run
```

---

## 📊 System Stats

- **Status:** 🟢 Running
- **Version:** 1.0.0
- **Server:** Uvicorn (FastAPI)
- **Port:** 8000
- **Bots:** 0 (ready to add)
- **Uptime:** See logs

---

## 🎉 You're All Set!

**Next:** Run `make new-bot` to create your first bot, or open http://localhost:8000 to explore the dashboard.

**Questions?** Check [SYSTEM_LAUNCHED.md](./SYSTEM_LAUNCHED.md) or review the relevant documentation file.

---

**Version:** 1.0.0 | **Date:** December 21, 2025
