from __future__ import annotations

from datetime import datetime
from typing import Literal, cast
from uuid import UUID

from pydantic import BaseModel, Field

RunStatus = Literal["pending", "running", "paused", "approval_required", "completed", "failed", "cancelled"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    timestamp: datetime


class Run(BaseModel):
    id: UUID
    workflow_key: str
    status: RunStatus
    vertical: Literal["finance", "retail", "saas"]
    total_cost_usd: float = 0.0
    step_count: int = 0


class RunDetail(Run):
    skill_name: str
    pending_approval: bool = False
    approval_role: str | None = None
    policy_citations: list[str] = Field(default_factory=list)
    tool_trace: list[dict[str, object]] = Field(default_factory=list)
    outcome: dict[str, object] | None = None
    error: str | None = None


class CreateRunRequest(BaseModel):
    briefing_json: dict[str, object] = Field(default_factory=dict)
    vertical: Literal["finance", "retail", "saas"]
    skill_name: str


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str


class MemorySearchRequest(BaseModel):
    query: str
    namespace: str
    memory_type: Literal["episodic", "semantic", "procedural", "working"] | None = None
    k: int = Field(default=5, ge=1, le=20)
    decay_weighted: bool = True
    min_trust: float = Field(default=0.0, ge=0.0, le=1.0)


def api_status(status: str) -> RunStatus:
    if status in {"pending", "running", "paused", "approval_required", "completed", "failed", "cancelled"}:
        return cast(RunStatus, status)
    return "failed"
