from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

RunStatus = Literal[
    "pending",
    "running",
    "paused",
    "approval_required",
    "completed",
    "failed",
    "cancelled",
]
RunVertical = Literal["finance", "retail", "saas"]
StepType = Literal["plan", "act", "observe", "verify", "retry", "human_gate", "complete"]
ApprovalStatus = Literal["approved", "rejected", "timeout"]


class RunRecord(BaseModel):
    id: UUID
    workflow_key: str
    status: RunStatus = "pending"
    vertical: RunVertical | None = None
    briefing_json: dict[str, Any] = Field(default_factory=dict)
    checkpoint_json: dict[str, Any] | None = None
    total_cost_usd: float = 0.0
    step_count: int = 0
    agent_id: UUID | None = None
    user_id: UUID | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime | None = None


class RunStepRecord(BaseModel):
    id: UUID
    run_id: UUID
    step_type: StepType
    tool_name: str | None = None
    risk_tier: str | None = None
    status: str
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    latency_ms: int | None = None
    cost_usd: float = 0.0
    span_json: dict[str, Any] | None = None
    created_at: datetime | None = None


class ApprovalRecord(BaseModel):
    id: UUID
    run_id: UUID
    action_type: str
    action_payload: dict[str, Any] = Field(default_factory=dict)
    arp_json: dict[str, Any] | None = None
    approver_role: str
    decision: ApprovalStatus | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
    created_at: datetime | None = None
