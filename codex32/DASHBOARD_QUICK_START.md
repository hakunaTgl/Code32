# 🎯 Codex-32 Dashboard Quick Start

## Access the Dashboard

**URL**: http://localhost:8000/api/v1/dashboard

The dashboard loads automatically with your current system state and refreshes every 5 seconds.

## What You See

### 🟢 System Health Card
At the top, you'll see your system status:
- **Healthy** 🟢 - All systems operational
- **Degraded** 🟡 - Some bots deploying
- **Critical** 🔴 - Failures detected

### 📊 Statistics
Six colorful cards showing:
- **Total Bots** - How many bots you have
- **Running** - Bots actively executing
- **Stopped** - Bots available to start
- **Deploying** - Bots being launched
- **Failed** - Bots with errors
- **Incidents** - Logged system events

### 💡 Next Steps
Contextual recommendations based on your system state:
- First time? See "Create your first bot"
- Bots exist but not running? See "Start one!"
- Errors detected? See "Check incidents"

### 🤖 Bot Inventory
Table showing all your bots with:
- **Bot ID** - Unique identifier
- **Name** - Human-friendly name
- **Status** - Current state badge
- **Role** - Bot's assigned role
- **Actions** - Buttons to View, Start, or Stop

## Common Actions

### Create a New Bot

1. Click the **"Create Bot"** button in the Next Steps section
2. Enter a bot name when prompted
3. Click OK
4. Dashboard refreshes automatically
5. New bot appears in the inventory table

### Start a Bot

1. Find the bot in the table
2. Click the **"Start"** button
3. Confirm the action
4. Watch the status change to "Running"

### Stop a Bot

1. Find the running bot in the table
2. Click the **"Stop"** button
3. Confirm the action
4. Status changes to "Stopped"

### View Bot Details

1. Click the **"View"** button next to a bot
2. A popup shows the bot ID and API endpoint

## Dashboard Behavior

- **Auto-Refresh**: Every 5 seconds the dashboard fetches latest data
- **No Manual Refresh Needed**: Changes appear automatically
- **Real-Time Status**: See bot status changes instantly
- **Mobile Friendly**: Works on phones and tablets

## Status Badges Explained

| Badge | Meaning |
|-------|---------|
| ▶️ Running | Bot is actively executing |
| ⏹️ Stopped | Bot exists but is not running |
| ⏳ Deploying | Bot is being started/configured |
| ❌ Failed | Bot encountered an error |
| ✨ Created | Bot was just created |

## Color Legend

| Color | Meaning |
|-------|---------|
| 🟢 Green | Running/Healthy |
| 🔵 Blue | Deploying/Info |
| ⚪ Gray | Stopped/Idle |
| 🔴 Red | Failed/Error |

## Tips & Tricks

### Monitor System Health
- Watch the health indicator at the top
- If it turns yellow/red, check the recommendations
- Critical issues show in the "Incidents" count

### Bulk Operations
- Start multiple bots by clicking Start on each
- Stop all bots before major updates
- Check incidents after failures

### Integration with API
- The dashboard uses the same REST API
- Everything you do here can be done via `/docs`
- Advanced users can use the API directly

### Performance
- Dashboard works on slow connections
- 5-second refresh keeps it responsive
- No WebSocket overhead - just HTTP polling

## Troubleshooting

**Dashboard is blank?**
- Wait 5-10 seconds for API to initialize
- Check that Docker containers are running
- Refresh the page (Ctrl+R or Cmd+R)

**Buttons not working?**
- Check browser console (F12 → Console tab)
- Verify API is running: `docker compose ps`
- Try refreshing the page

**Changes not showing?**
- Dashboard updates every 5 seconds automatically
- Try refreshing manually if needed
- Check that bot is actually running

**Need more help?**
- Visit API Docs: http://localhost:8000/docs
- Check system status: http://localhost:8000/api/v1/guide/status
- View incidents: http://localhost:8000/api/v1/self/incidents

## Quick Links

| Link | Purpose |
|------|---------|
| [Dashboard](http://localhost:8000/api/v1/dashboard) | This page |
| [API Docs](http://localhost:8000/docs) | Interactive API explorer |
| [Guide](http://localhost:8000/api/v1/guide/hello) | System onboarding |
| [Bot API](http://localhost:8000/api/v1/bots) | Raw API endpoint |
| [Health](http://localhost:8000/health) | System health check |

---

**Ready to build amazing bots?** Start by clicking "Create Bot" on the dashboard! 🚀
