"""Bot management API.

Implements the endpoints referenced in README:
- CRUD for bots
- start/stop operations

This router uses the file-based SecureRegistry for persistence.
"""

from __future__ import annotations

from datetime import datetime
from app.utils import utcnow
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.bot_registry import BotStatus, SecureRegistry
from app.dependencies import get_registry, get_executor
from app.adaptive_executor import AdaptiveExecutor

router = APIRouter(
    prefix="/api/v1/bots",
    tags=["bots"],
)


@router.get("", summary="List all bots", response_description="Array of bot configurations with current status")
def list_bots(registry: SecureRegistry = Depends(get_registry)) -> Dict[str, Any]:
    """
    Retrieve all registered bots in your inventory.

    **Returns:**
    - `bots`: Array of bot objects, each with id, name, status, and configuration
    - `total`: Total number of bots in the system
    - `next_steps`: Suggested actions based on current inventory
    """
    all_bots = [dict(b) if not isinstance(b, dict) else b for b in registry.get_all_bots()]
    stats = registry.get_registry_stats()

    next_steps = []
    if not all_bots:
        next_steps.append("POST /api/v1/bots - Create your first bot")
    else:
        running = stats.get("active_bots", 0)
        total = stats.get("total_bots", 0)
        if running == 0:
            next_steps.append(f"POST /api/v1/bots/{{bot_id}}/start - Start one of your {total} bot(s)")
        next_steps.append("GET /api/v1/bots/{{bot_id}} - View bot details")

    return {
        "bots": all_bots,
        "total": len(all_bots),
        "stats": stats,
        "next_steps": next_steps,
        "help": "Use POST /api/v1/bots with bot config JSON to create a new bot"
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new bot", response_description="Newly created bot with auto-assigned timestamps")
def create_bot(
    bot: Dict[str, Any],
    registry: SecureRegistry = Depends(get_registry),
) -> Dict[str, Any]:
    """
    Register a new autonomous bot in the system.

    **Require in JSON body:**
    - `id`: Unique bot identifier (string, e.g., "my-bot-001")
    - `name`: Human-readable bot name
    - `role`: Bot's function/role (e.g., "analyst", "task-runner")

    **Optional fields:**
    - `description`: What this bot does
    - `deployment_config`: Container/deployment settings

    **Auto-set by system:**
    - `created_at`: Server timestamp
    - `updated_at`: Server timestamp
    - `status`: Initially "created"
    """
    # Ensure created/updated timestamps are set server-side
    bot.setdefault("created_at", utcnow().isoformat())
    bot["updated_at"] = utcnow().isoformat()
    bot.setdefault("status", BotStatus.CREATED.value)

    try:
        result = registry.register_bot(bot)
        return {
            **result,
            "message": f"✓ Bot '{result.get('name')}' created successfully",
            "next_steps": [
                f"GET /api/v1/bots/{result.get('id')} - View this bot",
                f"POST /api/v1/bots/{result.get('id')}/start - Start this bot"
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{bot_id}", summary="Get bot details", response_description="Full bot configuration and current status")
def get_bot(
    bot_id: str,
    registry: SecureRegistry = Depends(get_registry),
) -> Dict[str, Any]:
    """
    Retrieve full details for a specific bot by ID.

    **Response includes:**
    - Bot configuration (id, name, role, description)
    - Current status (created, deploying, running, stopped, failed)
    - Timestamps (created_at, updated_at)
    - Deployment config and error info (if any)
    """
    bot = registry.get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_id}' not found. Use GET /api/v1/bots to list available bots."
        )
    bot_dict = dict(bot) if not isinstance(bot, dict) else bot
    status_val = str(bot_dict.get("status", "unknown")).lower()

    # Suggest actions based on current status
    next_steps = []
    if status_val in {"created", "stopped", "failed"}:
        next_steps.append(f"POST /api/v1/bots/{bot_id}/start - Start this bot")
    elif status_val == "running":
        next_steps.append(f"POST /api/v1/bots/{bot_id}/stop - Stop this bot")
    next_steps.append(f"PUT /api/v1/bots/{bot_id} - Update bot configuration")
    next_steps.append(f"DELETE /api/v1/bots/{bot_id} - Remove this bot")

    return {
        **bot_dict,
        "next_steps": next_steps
    }


@router.put("/{bot_id}", summary="Update bot configuration", response_description="Updated bot object")
def update_bot(
    bot_id: str,
    bot: Dict[str, Any],
    registry: SecureRegistry = Depends(get_registry),
) -> Dict[str, Any]:
    """
    Update an existing bot's configuration.

    **Important:**
    - The `id` in the JSON body must match the URL `{bot_id}`
    - `updated_at` is automatically set by the server
    - Most fields (name, role, description, config) are updateable
    """
    if bot_id != bot.get("id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mismatch: URL bot_id='{bot_id}' must match JSON id='{bot.get('id')}'"
        )

    bot["updated_at"] = utcnow().isoformat()
    try:
        result = registry.update_bot(bot)
        return {
            **result,
            "message": "✓ Bot configuration updated",
            "next_steps": [
                f"GET /api/v1/bots/{bot_id} - View updated bot",
                f"POST /api/v1/bots/{bot_id}/start - Start bot if needed"
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{bot_id}", summary="Delete a bot", status_code=status.HTTP_200_OK)
def delete_bot(
    bot_id: str,
    registry: SecureRegistry = Depends(get_registry),
) -> Dict[str, Any]:
    """
    Permanently remove a bot from the system.

    **Warning:** This action cannot be undone.
    Ensure the bot is stopped before deletion.
    """
    ok = registry.unregister_bot(bot_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_id}' not found or already deleted"
        )
    return {
        "status": "deleted",
        "bot_id": bot_id,
        "message": f"✓ Bot '{bot_id}' has been removed from the system",
        "next_steps": [
            "GET /api/v1/bots - View remaining bots",
            "POST /api/v1/bots - Create a new bot"
        ]
    }


@router.post("/{bot_id}/start", summary="Start a bot", response_description="Startup status and next steps")
async def start_bot(
    bot_id: str,
    executor: AdaptiveExecutor = Depends(get_executor),
    registry: SecureRegistry = Depends(get_registry),
) -> dict:
    """
    Launch a bot and begin its execution.

    The bot is deployed in a container and enters the "running" state.
    Use GET /api/v1/bots/{bot_id} to monitor status.
    """
    bot = registry.get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_id}' not found. Use GET /api/v1/bots to list available bots."
        )

    bot_dict = dict(bot) if not isinstance(bot, dict) else bot

    if str(bot_dict.get("status")) in {BotStatus.RUNNING.value, BotStatus.DEPLOYING.value}:
        return {
            "status": "already_running",
            "bot_id": bot_id,
            "message": f"✓ Bot is already {bot_dict.get('status')}",
            "next_steps": [
                f"GET /api/v1/bots/{bot_id} - Check current status",
                f"POST /api/v1/bots/{bot_id}/stop - Stop this bot"
            ]
        }

    try:
        await executor.run_bot(bot_dict)
        return {
            "status": "ok",
            "bot_id": bot_id,
            "message": f"✓ Bot '{bot_dict.get('name', bot_id)}' is starting...",
            "next_steps": [
                f"GET /api/v1/bots/{bot_id} - Monitor bot status",
                f"POST /api/v1/bots/{bot_id}/stop - Stop if needed"
            ]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/{bot_id}/stop", summary="Stop a running bot", response_description="Shutdown confirmation")
async def stop_bot(
    bot_id: str,
    reason: Optional[str] = None,
    executor: AdaptiveExecutor = Depends(get_executor),
    registry: SecureRegistry = Depends(get_registry),
) -> dict:
    """
    Gracefully shut down a running bot.

    **Parameters:**
    - `reason` (optional): A message explaining why the bot is being stopped

    The bot is cleanly terminated and container resources are freed.
    """
    bot = registry.get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_id}' not found"
        )

    try:
        ok = await executor.stop_bot(bot_id, reason=reason or "Stopped via API")
        if not ok:
            return {
                "status": "not_running",
                "bot_id": bot_id,
                "message": "Bot is not currently running",
                "next_steps": [
                    f"POST /api/v1/bots/{bot_id}/start - Start this bot"
                ]
            }
        return {
            "status": "ok",
            "bot_id": bot_id,
            "message": f"✓ Bot '{bot_id}' has been stopped",
            "next_steps": [
                f"GET /api/v1/bots/{bot_id} - View bot status",
                f"POST /api/v1/bots/{bot_id}/start - Start again if needed"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/{bot_id}/deploy-config", summary="Update bot deployment settings")
def update_deploy_config(
    bot_id: str,
    deployment_config: Dict[str, Any],
    registry: SecureRegistry = Depends(get_registry),
) -> Dict[str, Any]:
    """
    Modify container deployment settings for a bot.

    **Common settings:**
    - `image`: Container image to use
    - `memory_limit`: RAM allocation (e.g., "512m")
    - `cpu_limit`: CPU allocation (e.g., "0.5")
    - `environment_vars`: Dict of env vars to pass to container

    **Note:** Changes take effect on next bot start.
    """
    bot = registry.get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bot '{bot_id}' not found"
        )

    bot = dict(bot) if not isinstance(bot, dict) else bot
    bot["deployment_config"] = deployment_config
    bot["updated_at"] = utcnow().isoformat()

    try:
        result = registry.update_bot(bot)
        return {
            **result,
            "message": "✓ Deployment configuration updated",
            "note": "Restart the bot for changes to take effect",
            "next_steps": [
                f"POST /api/v1/bots/{bot_id}/stop - Stop the bot",
                f"POST /api/v1/bots/{bot_id}/start - Restart with new config"
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
