# ⚡ Dashboard Quick Reference

## 🚀 Quick Start

```
1. Open: http://localhost:8000/dashboard/
2. Click: ➕ Create Bot
3. Type: Any name (e.g., "My Bot")
4. Click: Create Bot
5. Click: ▶️ Start
6. Done! Bot is running 🟢
```

---

## 📍 Dashboard Sections

### Top: Header & Status
```
🤖 Codex-32          [🟢 HEALTHY]
```

### Middle: Quick Stats
```
[5] Total  [3] Running  [1] Stopped  [1] Failed  [0] Incidents
```

### Bottom: Bot List
```
Bot Name
[▶️ Start] [🗑️ Delete]  ← All actions here
```

---

## 🎯 One-Click Actions

| Button | What It Does | When Available |
|--------|------|-----------|
| ➕ | Create new bot | Always |
| ▶️ | Start bot | When stopped |
| ⏹️ | Stop bot | When running |
| 🗑️ | Delete bot | Always |
| 🔄 | Refresh now | Always |
| 🆘 | View incidents | Always |
| 📖 | API docs | Always |

---

## 🎨 Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 | RUNNING | Bot is active |
| 🟡 | STOPPED | Bot is paused |
| 🔴 | FAILED | Bot has error |
| ✨ | CREATED | Bot ready to start |

---

## 💡 System Health

| Indicator | Meaning | Action |
|-----------|---------|--------|
| 🟢 HEALTHY | Everything OK | Keep going! |
| 🟡 READY | No bots running | Start some bots |
| 🔴 CRITICAL | Bots failed | Click 🆘 Incidents |

---

## ⌚ Auto-Refresh

- Dashboard updates **every 3 seconds**
- No need to refresh manually
- Real-time monitoring built-in

---

## 🐛 Troubleshooting

**Can't see dashboard?**
- Check: `http://localhost:8000/dashboard/`
- Restart API: `python3 main.py`

**No bots showing?**
- They might not exist yet
- Click ➕ **Create Bot** to add one

**Status won't update?**
- Try ▶️ manually refresh
- Or Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)

**API not responding?**
- Check: `lsof -i :8000`
- Restart: `python3 main.py > logs.txt 2>&1 &`

---

## 📱 Works On

✅ Desktop Computer
✅ Laptop / Tablet  
✅ Mobile Phone
✅ Any Modern Browser

---

## 🎓 Learning Path

**Beginner**: Use dashboard only
↓
**Intermediate**: Mix dashboard + API docs
↓
**Advanced**: Full API automation

---

## 🔗 Other URLs

| URL | Purpose |
|-----|---------|
| `/dashboard/` | **This dashboard** |
| `/docs` | Full API documentation |
| `/api/v1/bots` | Bot list (JSON) |
| `/health` | System health check |
| `/api/v1/guide/status` | Detailed status |

---

**Version**: 1.0.0  
**Last Updated**: December 22, 2025  
**Status**: ✅ Production Ready

🎉 Start managing bots now: `http://localhost:8000/dashboard/`
