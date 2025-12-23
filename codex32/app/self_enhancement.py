"""Approval-gated self-enhancement pipeline.

This is intentionally *safe by default*:
- The system can propose changes as patch bundles.
- Nothing is applied unless explicitly approved with an admin token.
- All proposals and actions are recorded to an audit log.

The implementation is file-backed to keep the solution "free" and simple.
It’s compatible with the project’s existing atomic-write registry model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from app.utils import atomic_save_json, load_json
from app.utils import utcnow


@dataclass
class PatchProposal:
    proposal_id: str
    title: str
    goal: str
    created_at: str
    status: str  # proposed|approved|rejected|applied
    diff: str
    rationale: str
    risks: List[str]
    tests: List[str]
    approved_at: Optional[str] = None
    applied_at: Optional[str] = None
    rejected_at: Optional[str] = None
    reviewer: Optional[str] = None


class PatchStore:
    def __init__(self, path: str = "codex32_patch_proposals.json"):
        self.path = Path(path)

    def _load(self) -> Dict:
        return load_json(str(self.path)) if self.path.exists() else {"proposals": []}

    def _save(self, data: Dict) -> None:
        atomic_save_json(str(self.path), data)

    def list(self) -> List[PatchProposal]:
        data = self._load()
        return [PatchProposal(**p) for p in data.get("proposals", [])]

    def get(self, proposal_id: str) -> Optional[PatchProposal]:
        for p in self.list():
            if p.proposal_id == proposal_id:
                return p
        return None

    def add(self, proposal: PatchProposal) -> PatchProposal:
        data = self._load()
        data.setdefault("proposals", []).append(asdict(proposal))
        self._save(data)
        return proposal

    def update(self, proposal: PatchProposal) -> PatchProposal:
        data = self._load()
        proposals = data.get("proposals", [])
        for i, p in enumerate(proposals):
            if p.get("proposal_id") == proposal.proposal_id:
                proposals[i] = asdict(proposal)
                data["proposals"] = proposals
                self._save(data)
                return proposal
        # If not found, add
        return self.add(proposal)


def make_proposal_id(title: str, goal: str) -> str:
    h = hashlib.sha256(f"{title}|{goal}|{utcnow().isoformat()}".encode()).hexdigest()[:12]
    return f"patch-{h}"


def propose_patch(title: str, goal: str, diff: str, rationale: str, risks: List[str], tests: List[str]) -> PatchProposal:
    return PatchProposal(
        proposal_id=make_proposal_id(title, goal),
        title=title,
        goal=goal,
    created_at=utcnow().isoformat(),
        status="proposed",
        diff=diff,
        rationale=rationale,
        risks=risks,
        tests=tests,
    )


def approve_proposal(store: PatchStore, proposal_id: str, reviewer: str) -> PatchProposal:
    p = store.get(proposal_id)
    if not p:
        raise KeyError("Proposal not found")
    if p.status not in {"proposed"}:
        raise ValueError(f"Cannot approve proposal in status {p.status}")
    p.status = "approved"
    p.approved_at = utcnow().isoformat()
    p.reviewer = reviewer
    return store.update(p)


def reject_proposal(store: PatchStore, proposal_id: str, reviewer: str, reason: str) -> PatchProposal:
    p = store.get(proposal_id)
    if not p:
        raise KeyError("Proposal not found")
    if p.status in {"applied", "rejected"}:
        raise ValueError(f"Cannot reject proposal in status {p.status}")
    p.status = "rejected"
    p.rejected_at = utcnow().isoformat()
    p.reviewer = reviewer
    # Append rejection reason into rationale for audit
    p.rationale = f"{p.rationale}\n\nRejected reason: {reason}".strip()
    return store.update(p)


class PatchApplyError(RuntimeError):
    pass


def apply_approved_proposal(store: PatchStore, proposal_id: str, reviewer: str) -> PatchProposal:
    """Apply an approved proposal.

    This function is intentionally simple and conservative:
    - Only applies proposals that are already approved.
    - Expects the diff to be informational; actual application is done by
      writing files via explicit, validated operations.

    In this repository environment, we keep the apply mechanism as a gate:
    it's ready for integration with a proper patch applier, but will refuse
    to apply unless the caller supplies a supported patch payload format.
    """
    p = store.get(proposal_id)
    if not p:
        raise KeyError("Proposal not found")
    if p.status != "approved":
        raise ValueError("Proposal must be approved before applying")

    # For safety, require a sentinel header in diff to indicate it was generated
    # by a trusted path that includes file targets.
    if "*** Begin Patch" not in (p.diff or ""):
        raise PatchApplyError(
            "Unsupported diff format. For safety, only unified patch bundles starting with '*** Begin Patch' are applyable."
        )

    # Mark as applied (actual file application should be performed by the operator / CI pipeline).
    # We keep the gate here to avoid autonomous code modification.
    p.status = "applied"
    p.applied_at = utcnow().isoformat()
    p.reviewer = reviewer
    return store.update(p)
