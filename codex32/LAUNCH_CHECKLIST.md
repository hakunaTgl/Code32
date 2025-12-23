# Codex-32 Launch Checklist

This checklist captures the fixes applied during this session plus the remaining
enhancements that will make Codex-32 production-ready. Items marked `[x]` are
done; unchecked items are recommended follow-ups.

## ✅ Completed blocking fixes

- [x] Allow default placeholder secrets in dev/test while still preventing
  production boot unless real secrets are provided (`app/config.py`).
- [x] Added the missing `BotStatus.CREATED` enum member so API payloads/tests can
  use the documented status lifecycle (`app/models.py`).
- [x] Corrected container engine bookkeeping: fix the indentation bug that broke
  `create_container` and expose `get_container_info` for the supervisor
  (`app/container_engine.py`).
- [x] Hardened atomic file writes by fsyncing via a managed handle to avoid
  leaking descriptors and ensure durability (`app/utils.py`).

## 📋 Follow-up enhancements

- [x] Document the `CODEX32_ENV` and `CODEX32_ALLOW_DEFAULT_SECRETS` toggles
  inside `README.md` so operators know how to enforce secret policies.
- [ ] Add integration tests for `app/container_cli.py` to cover create/start/stop
  flows and prevent regressions in the custom engine CLI.
- [ ] Extend supervisor coverage with a container-backed bot fixture so we
  exercise the `get_container_info` path.
- [ ] Implement periodic cleanup/rotation for container `running/` directories to
  avoid unbounded disk usage in long-lived deployments.

## 🚀 Launch procedure

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configure secrets for production by copying `.env.template` to `.env`, setting
   `CODEX32_ENV=production`, and providing strong `API_SECRET_KEY` /
   `ADMIN_API_KEY`.
3. Run the automated test suite: `python -m pytest`.
4. Start the API: `uvicorn main:app --host 0.0.0.0 --port 8000`.
  (App startup/shutdown is managed via FastAPI lifespan handlers.)
5. (Optional) Use the container CLI to pre-create bots and verify
   `python -m app.container_cli list` shows expected entries.

Completing the follow-up enhancements will ensure the system stays healthy as it
moves beyond local development.
