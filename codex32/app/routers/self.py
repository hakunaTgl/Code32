"""Self-awareness and self-enhancement APIs.

Design goals:
- "Free" and local-first: file-backed storage, no external services.
- Safe-by-default: self-enhancement requires ADMIN_API_KEY approval.
- Useful operational visibility: expose capabilities, runtime state, and incidents.
"""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Header

from app.config import settings
from app.dependencies import get_registry, get_executor
from app.bot_registry import SecureRegistry
from app.adaptive_executor import AdaptiveExecutor
from app.supervisor import get_supervisor
from app.self_enhancement import (
    PatchStore,
    propose_patch,
    approve_proposal,
    reject_proposal,
    apply_approved_proposal,
    PatchApplyError,
)

router = APIRouter(prefix="/api/v1/self", tags=["self"])


def _require_admin(api_key: Optional[str]) -> None:
    if not api_key or api_key != settings.ADMIN_API_KEY.get_secret_value():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin API key")


@router.get("/capabilities")
def capabilities() -> dict:
    return {
        "self_healing": True,
        "self_awareness": True,
        "self_enhancement": {
            "enabled": True,
            "mode": "proposal-and-approve",
            "applies_changes": "only_with_admin_api_key",
        },
        "container_engine": "custom",
        "free_mode": True,
    }


@router.get("/runtime")
def runtime_state(
    registry: SecureRegistry = Depends(get_registry),
    executor: AdaptiveExecutor = Depends(get_executor),
) -> dict:
    bots = registry.get_all_bots()
    supervisor = get_supervisor()

    return {
        "bots_total": len(bots),
        "bots_running": [b.id for b in bots if b.status.value == "running"],
        "executor": {
            "running_processes": list(executor.running_processes.keys()),
            "running_containers": executor.running_containers,
        },
        "supervisor": {
            "enabled": bool(supervisor),
        },
    }


@router.get("/incidents")
def recent_incidents(limit: int = 200) -> list:
    supervisor = get_supervisor()
    if not supervisor:
        return []
    return supervisor.incidents.tail(limit=limit)


@router.get("/patches")
def list_patches(x_admin_api_key: Optional[str] = Header(default=None)) -> dict:
    _require_admin(x_admin_api_key)
    store = PatchStore()
    proposals = store.list()
    return {
        "count": len(proposals),
        "proposals": [
            {
                "proposal_id": p.proposal_id,
                "title": p.title,
                "goal": p.goal,
                "status": p.status,
                "created_at": p.created_at,
            }
            for p in proposals
        ],
    }


@router.post("/patches/propose", status_code=status.HTTP_201_CREATED)
def propose(
    title: str,
    goal: str,
    diff: str,
    rationale: str,
    risks: Optional[List[str]] = None,
    tests: Optional[List[str]] = None,
    x_admin_api_key: Optional[str] = Header(default=None),
) -> dict:
    _require_admin(x_admin_api_key)

    proposal = propose_patch(
        title=title,
        goal=goal,
        diff=diff,
        rationale=rationale,
        risks=risks or [],
        tests=tests or [],
    )
    store = PatchStore()
    store.add(proposal)
    return asdict_safe(proposal)


@router.get("/patches/{proposal_id}")
def get_patch(proposal_id: str, x_admin_api_key: Optional[str] = Header(default=None)) -> dict:
    _require_admin(x_admin_api_key)
    store = PatchStore()
    p = store.get(proposal_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return asdict_safe(p)


@router.post("/patches/{proposal_id}/approve")
def approve_patch(
    proposal_id: str,
    reviewer: str = "admin",
    x_admin_api_key: Optional[str] = Header(default=None),
) -> dict:
    _require_admin(x_admin_api_key)
    store = PatchStore()
    try:
        p = approve_proposal(store, proposal_id=proposal_id, reviewer=reviewer)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return asdict_safe(p)


@router.post("/patches/{proposal_id}/reject")
def reject_patch(
    proposal_id: str,
    reason: str,
    reviewer: str = "admin",
    x_admin_api_key: Optional[str] = Header(default=None),
) -> dict:
    _require_admin(x_admin_api_key)
    store = PatchStore()
    try:
        p = reject_proposal(store, proposal_id=proposal_id, reviewer=reviewer, reason=reason)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return asdict_safe(p)


@router.post("/patches/{proposal_id}/apply")
def apply_patch(
    proposal_id: str,
    reviewer: str = "admin",
    x_admin_api_key: Optional[str] = Header(default=None),
) -> dict:
    _require_admin(x_admin_api_key)
    store = PatchStore()
    try:
        p = apply_approved_proposal(store, proposal_id=proposal_id, reviewer=reviewer)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    except PatchApplyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return asdict_safe(p)


def asdict_safe(p) -> dict:
    # avoid importing dataclasses in FastAPI response layer for minimal overhead
    return {
        "proposal_id": p.proposal_id,
        "title": p.title,
        "goal": p.goal,
        "created_at": p.created_at,
        "status": p.status,
        "diff": p.diff,
        "rationale": p.rationale,
        "risks": p.risks,
        "tests": p.tests,
        "approved_at": p.approved_at,
        "applied_at": p.applied_at,
        "rejected_at": p.rejected_at,
        "reviewer": p.reviewer,
    }
