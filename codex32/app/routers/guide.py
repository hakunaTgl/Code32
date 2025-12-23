"""AI Guide / Companion API.

Goals
- User-friendly: give newcomers a clear next step.
- Local-first: no external model calls; everything is derived from local state.
- Stable contracts: return plain JSON (dict / list) and avoid Pydantic-heavy runtime paths.

This is intentionally a "smart guide" rather than a chatbot. It produces
contextual hints based on current system state (bots, supervisor, config).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.bot_registry import SecureRegistry
from app.dependencies import get_executor, get_registry
from app.supervisor import get_supervisor
from app.adaptive_executor import AdaptiveExecutor
from app.utils import get_timestamp


router = APIRouter(prefix="/api/v1/guide", tags=["guide"])


def _utc_now_iso() -> str:
    # keep time formatting consistent with other endpoints
    return get_timestamp()


router = APIRouter(
    prefix="/api/v1/guide",
    tags=["guide"],
)


def _utc_now_iso() -> str:
    # keep time formatting consistent with other endpoints
    return get_timestamp()


@router.get("/hello", summary="Friendly introduction", response_description="Welcome message with suggested first steps")
def hello() -> dict:
    """
    A friendly, predictable entrypoint for humans and demos.

    This is the best place to start if you're new to Codex-32.
    """
    return {
        "message": "👋 Hi — I'm the Codex-32 guide. I can help you get running.",
        "subtitle": "You're in the interactive assistant. I'll suggest your next steps based on system state.",
        "next": [
            {"title": "📋 Create a bot", "hint": "POST /api/v1/bots", "description": "Register your first autonomous bot"},
            {"title": "▶️ Start a bot", "hint": "POST /api/v1/bots/{bot_id}/start", "description": "Launch a bot and watch it run"},
            {"title": "📊 See system stats", "hint": "GET /api/v1/system/stats", "description": "View system health and metrics"},
            {"title": "🧠 Self-awareness", "hint": "GET /api/v1/self/runtime", "description": "Check Codex-32's own state"},
        ],
        "quick_links": {
            "all_bots": "GET /api/v1/bots",
            "docs": "GET /docs",
            "guide_status": "GET /api/v1/guide/status",
            "onboarding": "GET /api/v1/guide/onboarding"
        },
        "timestamp": _utc_now_iso(),
    }


@router.get("/onboarding", summary="Setup checklist", response_description="Step-by-step guide to get your first bot running")
def onboarding() -> dict:
    """
    A short, copy-ready onboarding checklist for getting started.

    Follow these steps in order to launch your first bot.
    """
    return {
        "title": "🚀 Codex-32 Quick Start Guide",
        "intro": "Follow these steps to create and run your first bot in less than 5 minutes.",
        "steps": [
            {
                "id": "1-create-bot",
                "number": 1,
                "title": "Create a bot",
                "description": "Register a new bot that points at a Python script or container.",
                "example": {
                    "method": "POST",
                    "path": "/api/v1/bots",
                    "body": {
                        "id": "my-first-bot",
                        "name": "My First Bot",
                        "role": "helper",
                        "description": "A friendly bot to help me learn"
                    }
                }
            },
            {
                "id": "2-start-bot",
                "number": 2,
                "title": "Start the bot",
                "description": "Launch your bot. It will run in a container with automatic fallback to local execution.",
                "example": {
                    "method": "POST",
                    "path": "/api/v1/bots/my-first-bot/start"
                }
            },
            {
                "id": "3-monitor",
                "number": 3,
                "title": "Monitor status",
                "description": "Check your bot's health, logs, and any incidents.",
                "example": {
                    "method": "GET",
                    "path": "/api/v1/bots/my-first-bot"
                }
            },
            {
                "id": "4-interact",
                "number": 4,
                "title": "Interact with your bot",
                "description": "Send commands, check output, or manage the bot lifecycle.",
                "example": {
                    "methods": ["GET (view)", "PUT (update)", "POST (action)", "DELETE (remove)"],
                    "path": "/api/v1/bots/my-first-bot"
                }
            }
        ],
        "next_steps": [
            "Explore /docs for interactive API documentation",
            "Read the README at the root of the project",
            "Check /api/v1/guide/status for current system insights"
        ],
        "timestamp": _utc_now_iso(),
    }


@router.get("/status", summary="System status and recommendations", response_description="Real-time system insights and guided suggestions")
def status(
    registry: SecureRegistry = Depends(get_registry),
    executor: AdaptiveExecutor = Depends(get_executor),
) -> dict:
    """
    Real-time system status with contextual recommendations.

    This endpoint analyzes the current state and suggests what you should do next:
    - No bots? Create one!
    - Bots not running? Start them!
    - Incidents detected? Review them!
    """

    bots = registry.get_all_bots()
    supervisor = get_supervisor()

    # registry returns BotRecord wrappers; keep response JSON-native
    # and compute counts in one pass to avoid repeated list scans.
    total = 0
    running = 0
    deploying = 0
    failed = 0
    bot_ids: list[str] = []
    for b in bots:
        bd = b.to_dict() if hasattr(b, "to_dict") else dict(b)
        bot_id = bd.get("id", "")
        if bot_id:
            bot_ids.append(bot_id)
        total += 1
        status_val = str((bd.get("status") or "")).lower()
        if status_val == "running":
            running += 1
        elif status_val == "deploying":
            deploying += 1
        elif status_val in {"failed", "error"}:
            failed += 1

    # Generate contextual recommendations based on state
    recommendations = []
    if total == 0:
        recommendations.append({
            "priority": "high",
            "message": "📝 Get started! Create your first bot",
            "action": "POST /api/v1/bots",
            "example": {"id": "my-bot", "name": "My Bot", "role": "assistant"}
        })
    elif running == 0 and total > 0:
        recommendations.append({
            "priority": "high",
            "message": "▶️ No bots running. Start one!",
            "action": f"POST /api/v1/bots/{bot_ids[0]}/start" if bot_ids else "POST /api/v1/bots/{{bot_id}}/start"
        })

    if failed > 0:
        recommendations.append({
            "priority": "high",
            "message": f"⚠️ {failed} bot(s) have failed. Check /api/v1/self/incidents",
            "action": "GET /api/v1/self/incidents"
        })

    if deploying > 0:
        recommendations.append({
            "priority": "low",
            "message": f"⏳ {deploying} bot(s) currently deploying. Be patient!",
            "action": f"GET /api/v1/bots/{bot_ids[0]}" if bot_ids else "GET /api/v1/bots"
        })

    return {
        "system_health": "healthy" if failed == 0 else "degraded" if failed < total else "critical",
        "bots": {
            "total": total,
            "running": running,
            "deploying": deploying,
            "failed": failed,
            "stopped": total - running - deploying - failed,
            "bot_ids": bot_ids,
        },
        "executor": {
            "running_processes": list(executor.running_processes.keys()),
            "running_containers": executor.running_containers,
        },
        "supervisor": {
            "enabled": bool(supervisor),
            "incidents_count": len(supervisor.incidents) if supervisor else 0,
        },
        "recommendations": recommendations,
        "helpful_links": {
            "api_docs": "/docs",
            "bot_inventory": "GET /api/v1/bots",
            "incidents": "GET /api/v1/self/incidents",
            "onboarding": "GET /api/v1/guide/onboarding"
        },
        "timestamp": _utc_now_iso(),
    }


@router.get("/recommendations")
def recommendations(
    registry: SecureRegistry = Depends(get_registry),
    executor: AdaptiveExecutor = Depends(get_executor),
) -> dict:
    """Actionable next steps based on current state."""

    state = status(registry=registry, executor=executor)
    bots_total = state["bots"]["total"]
    bots_running = state["bots"]["running"]
    incidents = state["supervisor"]["incidents_count"]

    recs: list[dict] = []

    if bots_total == 0:
        recs.append(
            {
                "priority": "high",
                "title": "Create your first bot",
                "reason": "No bots are registered yet.",
                "action": {"method": "POST", "path": "/api/v1/bots"},
            }
        )
    elif bots_running == 0:
        # suggest starting the first bot id we know
        bot_id = (state["bots"]["bot_ids"] or [None])[0]
        recs.append(
            {
                "priority": "high",
                "title": "Start a bot",
                "reason": "Bots exist but none are running.",
                "action": {"method": "POST", "path": f"/api/v1/bots/{bot_id}/start"},
            }
        )

    if incidents:
        recs.append(
            {
                "priority": "medium",
                "title": "Review recent incidents",
                "reason": "The supervisor recorded incidents.",
                "action": {"method": "GET", "path": "/api/v1/self/incidents"},
            }
        )

    # always provide a low-friction suggestion
    recs.append(
        {
            "priority": "low",
            "title": "Open API docs",
            "reason": "Browse and try endpoints interactively.",
            "action": {"method": "GET", "path": "/docs"},
        }
    )

    return {
        "recommendations": recs,
        "state": state,
    }
