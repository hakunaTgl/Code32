# 🤖 Intelligent Bot Builder - User Guide

**Version:** 2.0 (AI-Enhanced)  
**Date:** December 21, 2025  
**Focus:** Making bot creation effortless for non-technical users

---

## 🎯 What's New

### Before (Code-Based)
- Required Python knowledge
- Manual configuration editing
- Complex setup process
- Technical YAML syntax
- Limited templates

### Now (AI-Powered, User-Friendly)
- ✨ **Describe in Plain English** - Just tell it what you want
- ✅ **AI Generates Everything** - Code, configs, requirements
- 🎨 **Modern Dashboard** - Visual interface, no terminal needed
- ⚡ **One-Click Creation** - From description to deployment-ready bot in seconds
- 🧠 **Intelligent Templates** - Auto-selects best template based on your needs

---

## 🚀 Quick Start

### Access the New Dashboard

```bash
# The intelligent dashboard is now live!
open http://localhost:8000/api/v1/bots/dashboard
```

Or navigate to the main dashboard which now includes intelligent bot creation:

```bash
open http://localhost:8000
```

### Create Your First Bot (No Coding!)

**Option 1: Using the Dashboard (Recommended for everyday users)**

1. Go to http://localhost:8000/api/v1/bots/dashboard
2. Click **"✨ Create Bot (No Coding!)"**
3. Describe what you want: 
   ```
   Monitor my orders database every 5 seconds and send new orders to our fulfillment API
   ```
4. Click **Create**
5. Done! Your bot is ready to deploy

**Option 2: Using the API**

```bash
curl -X POST http://localhost:8000/api/v1/bots/create-from-description \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Monitor orders database every 5 seconds and send new orders to fulfillment API"
  }'
```

**Response:**
```json
{
  "success": true,
  "bot_name": "monitor_orders",
  "message": "✨ Bot 'monitor_orders' created successfully!",
  "ready_to_deploy": true,
  "features": ["database", "api", "error_handling"]
}
```

---

## 💡 How to Write Effective Bot Descriptions

The AI bot builder understands natural language. Here's how to get the best results:

### Good Descriptions (Clear & Detailed)

✅ **"Every night at midnight, fetch the previous day's sales from our database, analyze the totals by region, and email the report to management"**
- When: Every night at midnight
- Data source: Database
- What to do: Analyze sales
- Output: Email report

✅ **"Monitor the support tickets table continuously. When a new high-priority ticket arrives, immediately notify the team via Slack and create a task in our project management system"**
- When: Continuously (real-time)
- Source: Tickets table
- Trigger: High-priority
- Actions: Slack + project management

✅ **"Process uploaded CSV files: remove duplicate rows, validate email addresses, standardize phone numbers, then save the clean data back to PostgreSQL"**
- Input: CSV files
- Processing: Data cleaning
- Output: PostgreSQL

### Less Good Descriptions (Too Vague)

❌ "Process data"
- Too vague about what data and what processing

❌ "Make it faster"
- Doesn't specify what bot or what tasks

❌ "Handle errors"
- Too generic without context

### Elements to Include

1. **Frequency/When:**
   - "every 5 seconds", "every hour", "daily", "on-demand", "continuously", "at midnight"

2. **Data Source:**
   - "database", "API", "CSV files", "external service", "webhook", "queue"

3. **What It Does:**
   - "process", "analyze", "transform", "collect", "notify", "monitor"

4. **Output/Result:**
   - "save to database", "call API", "send email", "alert team", "create report"

5. **Special Features:**
   - "handle errors", "retry on failure", "log details", "notify on success"

---

## 🎯 Task Types (AI Auto-Detects)

The AI understands different bot purposes and auto-configures them:

### Worker Bot
- **Best for:** Data processing, transformations, calculations
- **Auto-detected keywords:** "process", "transform", "convert", "change"
- **Example:** "Process CSV files and transform them to JSON"

### Collector Bot
- **Best for:** Gathering and aggregating data
- **Auto-detected keywords:** "collect", "gather", "fetch", "scrape", "retrieve"
- **Example:** "Collect weather data from OpenWeather API every hour"

### API Bot
- **Best for:** External API calls and integrations
- **Auto-detected keywords:** "call", "request", "API", "webhook", "http"
- **Example:** "Call our fulfillment API with new orders from the database"

### Analyzer Bot
- **Best for:** Data analysis and insights
- **Auto-detected keywords:** "analyze", "analyze", "examine", "study", "review"
- **Example:** "Analyze sales trends and generate monthly reports"

### Monitor Bot
- **Best for:** Health checking and alerting
- **Auto-detected keywords:** "monitor", "watch", "track", "observe", "check"
- **Example:** "Monitor server health and alert if CPU exceeds 80%"

---

## 📊 Frequency Modes (AI Auto-Detects)

The AI understands how often your bot should run:

### Continuous (24/7)
- **Keywords:** "continuous", "24/7", "always", "constantly", "real-time"
- **Use for:** Real-time monitoring, streaming data
- **Example:** "Continuously monitor orders and process them as they arrive"

### Scheduled
- **Keywords:** "daily", "weekly", "hourly", "every X minutes/hours"
- **Use for:** Regular interval processing
- **Example:** "Every 5 seconds, check for new records"

### Triggered
- **Keywords:** "when", "on", "if", "triggered by event"
- **Use for:** Event-based processing
- **Example:** "When a file is uploaded, process it"

### Manual
- **Keywords:** "on-demand", "button", "user", "command"
- **Use for:** User-initiated operations
- **Example:** "When a user clicks process, run the analysis"

---

## 🎨 The New Dashboard Features

### 1. Quick Bot Creation Section
- Natural language input
- Template selector
- One-click creation

### 2. Your Bots Section
- Visual bot cards
- Status indicators (🟢 Active, ⚫ Inactive)
- Stats: Processed count, Error count
- Quick actions: Start, View, Delete

### 3. System Statistics
- Total Bots
- Active Bots
- Tasks Processed
- System Health

### 4. Activity Log
- Recent actions
- Creation history
- Status changes

---

## 🔌 API Endpoints

### Create Bot from Description

```bash
POST /api/v1/bots/create-from-description
Content-Type: application/json

{
  "description": "Your bot description here",
  "template": "worker",  # Optional: worker, collector, api, analyzer
  "complexity": "moderate",  # Optional: simple, moderate, advanced
  "frequency": "triggered"  # Optional: triggered, scheduled, continuous
}
```

### Test Description (Before Creating)

```bash
POST /api/v1/bots/test-description

{
  "description": "Your bot description"
}
```

**Response:** Shows what bot would be created without actually creating it.

### Get Bot Templates

```bash
GET /api/v1/bots/templates
```

**Response:** List of available templates with descriptions and icons.

### Get Examples

```bash
GET /api/v1/bots/examples
```

**Response:** Real example descriptions and what they create.

### Get Help

```bash
GET /api/v1/bots/help
```

**Response:** Tips and guidelines for writing effective bot descriptions.

---

## 📁 What Gets Created

When you create a bot from a description, the AI generates:

### 1. bot.py (Auto-Generated Code)
- Fully functional bot class
- Async/await pattern
- Task processing methods
- Status tracking
- Error handling
- Ready to customize

### 2. config.yaml (Configuration)
- Bot metadata
- Task type
- Input/output types
- Frequency settings
- Feature list
- Deployment config

### 3. requirements.txt (Dependencies)
- Auto-includes needed packages
- Based on detected features
- Ready to install

### Example Structure
```
bots/
└── my_monitor_bot/
    ├── bot.py              # Auto-generated, ready to customize
    ├── config.yaml         # Configuration
    ├── requirements.txt    # Dependencies
    └── README.md           # Documentation (auto-generated)
```

---

## 🎓 Examples You Can Try

### Example 1: Simple Data Processing
**Description:**
```
Monitor a CSV file location. When a new file appears, clean the data 
by removing duplicates, validate email addresses, and save to PostgreSQL database.
```

**What you get:**
- Bot type: Worker Bot
- Features: File handling, data validation, database storage
- Auto-generated code handles: File watching, CSV parsing, validation

### Example 2: Real-Time Monitoring
**Description:**
```
Monitor my orders database table continuously. Every time a new order arrives, 
immediately send it to the fulfillment API and update the order status to "processing".
```

**What you get:**
- Bot type: API Bot
- Frequency: Continuous
- Features: Database monitoring, API integration, error handling

### Example 3: Scheduled Reporting
**Description:**
```
Every morning at 9 AM, fetch yesterday's sales data from the database, 
calculate totals by region, generate charts, and email the report to all managers.
```

**What you get:**
- Bot type: Analyzer Bot
- Frequency: Scheduled (daily)
- Features: Database access, data analysis, email notifications

### Example 4: Webhook Handler
**Description:**
```
When our payment provider sends a webhook notification that a payment succeeded, 
mark the order as paid in our database and trigger the fulfillment process.
```

**What you get:**
- Bot type: Trigger Bot
- Frequency: Triggered (event-based)
- Features: Webhook handling, database updates, webhook calling

---

## 🔧 Customizing Generated Bots

The AI generates a great starting point. You can customize it:

### 1. Open the Generated Bot
```bash
nano bots/my_monitor_bot/bot.py
```

### 2. Find the TODO Section
```python
async def _transform_data(self, data):
    """Transform data (override this method)."""
    # TODO: Implement your transformation logic
    return data
```

### 3. Add Your Custom Logic
```python
async def _transform_data(self, data):
    """Clean and validate the data."""
    # Your actual implementation
    validated = []
    for row in data:
        if is_valid_email(row['email']):
            validated.append(row)
    return validated
```

### 4. Update Requirements
```bash
# Add any additional packages to requirements.txt
echo "email-validator==2.0.0" >> bots/my_monitor_bot/requirements.txt

# Install dependencies
pip install -r bots/my_monitor_bot/requirements.txt
```

### 5. Test Locally
```bash
cd bots/my_monitor_bot
python bot.py
```

### 6. Deploy
```bash
# Register with the system
curl -X POST http://localhost:8000/api/v1/bots/register \
  -H "Content-Type: application/json" \
  -d @config.yaml
```

---

## 📈 Complexity Levels

The AI detects complexity and generates appropriate code:

### Simple (Straightforward Logic)
- **Characteristics:** One or two operations, no complex processing
- **Example:** "Send me a reminder every morning"
- **Generated code:** Minimal dependencies, simple async flow

### Moderate (Typical Business Logic)
- **Characteristics:** API calls, database access, multiple steps
- **Example:** "Monitor orders and send to fulfillment API"
- **Generated code:** Full async patterns, error handling, logging

### Advanced (Complex Requirements)
- **Characteristics:** Machine learning, complex analysis, multi-source integration
- **Example:** "Analyze sales patterns using ML and generate predictions"
- **Generated code:** Advanced libraries, optimization, sophisticated error handling

---

## 🚫 Error Handling

The AI automatically includes error handling:

### Generated Error Handling
- Try/except blocks
- Logging of errors
- Error counting
- Graceful degradation
- Retry logic for transient failures

### Example
```python
async def process_task(self, task):
    try:
        # Your logic
        result = await self._do_something(task)
        self.processed_count += 1
        return {"status": "success", "result": result}
    except Exception as e:
        self.error_count += 1
        self.logger.error(f"Processing error: {e}")
        return {"status": "error", "message": str(e)}
```

---

## 🎯 Best Practices

1. **Be Specific**
   - ✅ "Monitor orders table for new records and call fulfillment API every 2 seconds"
   - ❌ "Handle orders"

2. **Include Timing**
   - ✅ "Every 5 minutes"
   - ❌ "Frequently"

3. **Mention Data Sources**
   - ✅ "From PostgreSQL database"
   - ❌ "Get data"

4. **Specify Outputs**
   - ✅ "Send to Slack and save to database"
   - ❌ "Do something with results"

5. **Test First**
   - Use `/api/v1/bots/test-description` to preview before creating

6. **Customize After**
   - The AI creates a great foundation
   - Add your specific business logic afterward

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8000/api/v1/bots/dashboard
- **Examples:** http://localhost:8000/api/v1/bots/examples
- **Help:** http://localhost:8000/api/v1/bots/help

---

## 🆘 Getting Help

### Get Examples
```bash
curl http://localhost:8000/api/v1/bots/examples
```

### Get Templates
```bash
curl http://localhost:8000/api/v1/bots/templates
```

### Get Help
```bash
curl http://localhost:8000/api/v1/bots/help
```

### Test Your Description
```bash
curl -X POST http://localhost:8000/api/v1/bots/test-description \
  -H "Content-Type: application/json" \
  -d '{"description": "Your description here"}'
```

---

## 📊 What Gets Auto-Detected

The AI automatically understands:

- **Task Type:** worker, collector, API, analyzer, monitor
- **Frequency:** continuous, scheduled, triggered, manual
- **Complexity:** simple, moderate, advanced
- **Input Type:** JSON, CSV, text, image, database
- **Output Type:** Same options
- **Required Features:** database, API, notifications, caching, scheduling, logging
- **Dependencies:** Auto-includes necessary Python packages

---

## 🎉 You're Ready!

You now have everything you need to create sophisticated bots without writing code:

1. ✅ Describe what you want in plain English
2. ✅ AI generates production-ready code
3. ✅ Customize if needed
4. ✅ Deploy with one click
5. ✅ Monitor via the beautiful dashboard

**Next Steps:**
1. Open http://localhost:8000/api/v1/bots/dashboard
2. Click "✨ Create Bot (No Coding!)"
3. Describe your bot
4. Click Create
5. Watch the magic happen! ✨

---

**Happy bot building!** 🤖

For questions, check `/api/v1/bots/help` or review the API docs at `/docs`.
