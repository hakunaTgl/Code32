# Bot Templates for Codex-32

Quick-start templates for common bot patterns. Each template is a working example you can customize.

## Available Templates

### 1. **Worker Bot** (`worker-bot/`)
Process individual tasks from a queue. Great for:
- Data processing pipelines
- API request handling
- Long-running computations
- ETL operations

```bash
python scripts/init-bot.py --template worker --name my_worker
```

### 2. **Collector Bot** (`collector-bot/`)
Gather data from multiple sources. Great for:
- Data aggregation
- Log collection
- Monitoring data gathering
- API data fetching

```bash
python scripts/init-bot.py --template collector --name data_gatherer
```

### 3. **API Bot** (`api-bot/`)
Expose custom endpoints. Great for:
- Domain-specific REST APIs
- Query processing
- Report generation
- Custom business logic

```bash
python scripts/init-bot.py --template api --name my_api
```

### 4. **ML Bot** (`ml-bot/`)
Run machine learning inference. Great for:
- Model predictions
- Classification tasks
- Anomaly detection
- Pattern recognition

```bash
python scripts/init-bot.py --template ml --name my_ml_bot
```

### 5. **Orchestrator Bot** (`orchestrator-bot/`)
Coordinate other bots. Great for:
- Workflow orchestration
- Multi-step processes
- Bot-to-bot communication
- Complex business processes

```bash
python scripts/init-bot.py --template orchestrator --name workflow_manager
```

## Using a Template

### Step 1: Initialize from Template
```bash
python scripts/init-bot.py --template worker --name my_bot
```

### Step 2: Customize the Bot
Edit `bots/my_bot/bot.py` and implement your logic

### Step 3: Test Locally
```bash
python bots/my_bot/bot.py
```

### Step 4: Deploy to Codex-32
```bash
curl -X POST http://localhost:8000/api/v1/bots/register \
  -H "Content-Type: application/json" \
  -d @bots/my_bot/config.yaml
```

## Template Structure

Each template includes:
- `bot.py` - Main bot implementation
- `config.yaml` - Configuration and metadata
- `requirements.txt` - Dependencies
- `tests/test_bot.py` - Unit tests
- `README.md` - Template-specific documentation

## Creating Custom Templates

Create a new template directory:
```
templates/my_template/
├── bot.py
├── config.yaml
├── requirements.txt
└── README.md
```

Then use it:
```bash
python scripts/init-bot.py --template my_template --name my_bot
```

## Documentation

- [Worker Bot Guide](./worker-bot/README.md)
- [Collector Bot Guide](./collector-bot/README.md)
- [API Bot Guide](./api-bot/README.md)
- [ML Bot Guide](./ml-bot/README.md)
- [Orchestrator Bot Guide](./orchestrator-bot/README.md)

## Examples

See the `docs/examples/` directory for complete working examples of each template in action.

---

**Need Help?** Check the main [Documentation Index](../DOCUMENTATION_INDEX.md) or the [Getting Started Guide](../docs/getting-started/quick-start.md)
