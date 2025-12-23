# Worker Bot Template

A simple worker bot that proces`ses tasks sequentially. Perfect for:
- Data processing pipelines
- API integrations
- Task automation
- Report generation

## Quick Start

### 1. Initialize from Template
```bash
python scripts/init-bot.py --template worker --name my_processor
```

### 2. Edit Your Bot Logic
```bash
nano bots/my_processor/bot.py
```

Modify the `process_task()` method with your custom logic.

### 3. Test Locally
```bash
cd bots/my_processor
python bot.py
```

### 4. Deploy
```bash
curl -X POST http://localhost:8000/api/v1/bots/register \
  -H "Content-Type: application/json" \
  -d @config.yaml
```

## Bot Lifecycle

```
Start → Wait for Task → Process → Store Result → Repeat
```

## Configuration

Edit `config.yaml`:

```yaml
name: my_worker
description: Custom worker bot
role: worker
version: "1.0"

deployment_config:
  cpu_request: "0.5"        # CPU cores
  memory_request: "256Mi"   # Memory
  replicas: 1
  
environment:
  LOG_LEVEL: INFO
  TASK_TIMEOUT: "300"       # seconds
```

## Customization Examples

### Example 1: Database Query Worker

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Process database query."""
    query = task.get("query")
    
    async with self.db_pool.acquire() as conn:
        result = await conn.fetch(query)
    
    return {"rows": len(result), "data": result}
```

### Example 2: API Call Worker

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Call external API."""
    url = task.get("url")
    params = task.get("params", {})
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()
```

### Example 3: ML Inference Worker

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Run ML inference."""
    data = task.get("data")
    
    result = self.model.predict([data])
    
    return {
        "prediction": result[0].tolist(),
        "confidence": float(result[0].max())
    }
```

## Testing

Run the included tests:

```bash
pytest tests/ -v
```

## Debugging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python bot.py
```

## Performance Tips

1. **Connection Pooling**: Reuse connections
2. **Batch Processing**: Process multiple tasks together
3. **Caching**: Cache frequently accessed data
4. **Timeouts**: Set task timeouts to prevent hangs
5. **Error Handling**: Implement retry logic for transient failures

## Monitoring

The bot automatically reports:
- Processed count
- Error count
- Uptime
- Last processed task

Access via API:
```bash
curl http://localhost:8000/api/v1/bots/{bot_id}/status
```

## Advanced Features

### Custom Error Handling

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Your processing logic
        return {"status": "success", "result": data}
    except TemporaryError as e:
        # Retry logic
        logger.warning(f"Temporary error, will retry: {e}")
        raise
    except PermanentError as e:
        # Skip with logging
        logger.error(f"Permanent error, skipping task: {e}")
        return {"status": "failed", "error": str(e)}
```

### Custom Metrics

```python
async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    
    result = await self.expensive_operation(task)
    
    duration = time.time() - start
    self.metrics.record_latency(duration)
    
    return result
```

## Documentation

- [Worker Bot Source](./bot.py)
- [Configuration](./config.yaml)
- [Tests](./tests/test_bot.py)
- [Full API Reference](../../docs/api-reference/bots.md)

## Troubleshooting

**Bot crashes on startup**
- Check logs: `tail -f logs/codex32.log`
- Verify dependencies: `pip install -r requirements.txt`
- Check configuration: `cat config.yaml`

**Tasks not processing**
- Check bot status: `curl http://localhost:8000/api/v1/bots/{id}`
- Verify task source configuration
- Check memory/CPU limits

**Performance issues**
- Monitor resource usage: `curl http://localhost:8000/api/v1/bots/{id}/metrics`
- Increase replicas in config.yaml
- Profile with `cProfile` or `py-spy`

## Next Steps

1. ✅ Implement `process_task()` method
2. ✅ Add unit tests in `tests/`
3. ✅ Configure `config.yaml`
4. ✅ Test locally
5. ✅ Deploy to Codex-32
6. ✅ Monitor in dashboard

---

**Questions?** See the [main documentation](../../docs/) or [examples](../../docs/examples/)
