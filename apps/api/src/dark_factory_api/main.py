from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    timestamp: datetime


class Run(BaseModel):
    id: UUID
    workflow_key: str
    status: Literal["pending", "running", "paused", "approval_required", "completed", "failed", "cancelled"]
    vertical: Literal["finance", "retail", "saas"]
    total_cost_usd: float = 0.0
    step_count: int = 0


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
    memory_type: Literal["episodic", "semantic", "procedural", "working"]
    k: int = Field(default=5, ge=1, le=20)
    decay_weighted: bool = True


app = FastAPI(
    title="Dark Factory OS Control Plane API",
    version="0.1.0",
    description="Governed agentic operations platform API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS: dict[UUID, Run] = {}

DEMO_RUNS: list[dict[str, object]] = [
    {
        "id": "demo-finance-ap",
        "workflow_key": "ap-exception-resolution",
        "status": "approval_required",
        "vertical": "finance",
        "total_cost_usd": 0.29,
        "step_count": 7,
        "summary": "Amount mismatch over approval threshold for Contoso Logistics.",
    },
    {
        "id": "demo-retail-promo",
        "workflow_key": "promo-rebalance",
        "status": "approval_required",
        "vertical": "retail",
        "total_cost_usd": 0.34,
        "step_count": 8,
        "summary": "Promotion margin drop requires price band approval.",
    },
    {
        "id": "demo-saas-incident",
        "workflow_key": "incident-triage",
        "status": "running",
        "vertical": "saas",
        "total_cost_usd": 0.21,
        "step_count": 6,
        "summary": "P1 billing-api incident spike after deployment.",
    },
]

DEMO_SKILLS = [
    {"name": "ap-exception-resolution", "vertical": "finance", "risk_tier": "medium", "eval_status": "seeded"},
    {"name": "spend-anomaly-detection", "vertical": "finance", "risk_tier": "medium", "eval_status": "seeded"},
    {"name": "promo-rebalance", "vertical": "retail", "risk_tier": "medium", "eval_status": "seeded"},
    {"name": "replenishment-control", "vertical": "retail", "risk_tier": "medium", "eval_status": "seeded"},
    {"name": "incident-triage", "vertical": "saas", "risk_tier": "medium", "eval_status": "seeded"},
    {"name": "churn-risk-investigation", "vertical": "saas", "risk_tier": "medium", "eval_status": "seeded"},
]

DEMO_APPROVALS: list[dict[str, object]] = [
    {
        "id": "apr-fin-001",
        "run_id": "demo-finance-ap",
        "action_type": "erp.post_payment",
        "approver_role": "finance-manager",
        "risk_tier": "financial",
        "status": "pending",
        "summary": "Approve invoice after PO correction for $12,500.",
        "evidence": ["POL-AP-12", "PO-88219", "INV-2042"],
    },
    {
        "id": "apr-ret-001",
        "run_id": "demo-retail-promo",
        "action_type": "pricing.set_price_band",
        "approver_role": "commercial-manager",
        "risk_tier": "financial",
        "status": "pending",
        "summary": "Adjust promo price band to protect margin while stock remains healthy.",
        "evidence": ["POL-PRICE-04", "CMP-100", "SKU-SW12"],
    },
]

DEMO_MEMORY: list[dict[str, object]] = [
    {
        "namespace": "finance.vendor_risk",
        "entity_key": "contoso-logistics",
        "memory_type": "semantic",
        "trust": 0.92,
        "summary": "Prior amount mismatches resolved after PO correction, but payments above threshold require review.",
    },
    {
        "namespace": "retail.campaign_history",
        "entity_key": "sparkling-water-12pk",
        "memory_type": "semantic",
        "trust": 0.89,
        "summary": "Margin drops often correlate with channel mix shift and supplier rebate timing.",
    },
    {
        "namespace": "saas.incident_history",
        "entity_key": "billing-api",
        "memory_type": "episodic",
        "trust": 0.86,
        "summary": "Recent P1 spikes followed deploys touching invoice preview and payment retry logic.",
    },
]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="dark-factory-api", timestamp=datetime.now(UTC))


@app.get("/api/runs", response_model=list[Run])
def list_runs() -> list[Run]:
    return list(RUNS.values())


@app.get("/api/demo/runs")
def list_demo_runs() -> list[dict[str, object]]:
    return DEMO_RUNS


@app.post("/api/runs", response_model=Run, status_code=201)
def create_run(payload: CreateRunRequest) -> Run:
    run = Run(
        id=uuid4(),
        workflow_key=payload.skill_name,
        status="pending",
        vertical=payload.vertical,
        total_cost_usd=0.0,
        step_count=0,
    )
    RUNS[run.id] = run
    return run


@app.get("/api/runs/{run_id}", response_model=Run)
def get_run(run_id: UUID) -> Run:
    try:
        return RUNS[run_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/runs/{run_id}/resume", status_code=202)
def resume_run(run_id: UUID, payload: ApprovalDecisionRequest) -> dict[str, str]:
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    run = RUNS[run_id]
    RUNS[run_id] = run.model_copy(update={"status": "running" if payload.decision == "approved" else "cancelled"})
    return {"status": "accepted"}


@app.get("/api/skills")
def list_skills() -> list[dict[str, str]]:
    return DEMO_SKILLS


@app.get("/api/approvals")
def list_approvals() -> list[dict[str, object]]:
    return DEMO_APPROVALS


@app.post("/api/approvals/{approval_id}/decision", status_code=202)
def decide_approval(approval_id: str, payload: ApprovalDecisionRequest) -> dict[str, str]:
    if approval_id not in {approval["id"] for approval in DEMO_APPROVALS}:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"status": "accepted", "decision": payload.decision}


@app.post("/api/memory/search")
def search_memory(payload: MemorySearchRequest) -> dict[str, object]:
    return {
        "query": payload.query,
        "namespace": payload.namespace,
        "matches": [
            {
                "entity_key": "demo-policy-context",
                "score": 0.91,
                "content": "Synthetic governed memory placeholder. Real retrieval lands in R4.",
            }
        ],
    }


@app.get("/api/memory/demo")
def memory_demo() -> list[dict[str, object]]:
    return DEMO_MEMORY


@app.get("/api/costs/summary")
def cost_summary() -> dict[str, object]:
    return {
        "total_usd": 0.84,
        "by_category": {"model_tokens": 0.55, "retrieval": 0.09, "tool_compute": 0.11, "human_review": 0.09},
        "by_vertical": {"finance": 0.29, "retail": 0.34, "saas": 0.21},
    }


@app.get("/api/evals/demo")
def eval_demo() -> dict[str, object]:
    return {
        "metrics": [
            {"workflow": "retail_promo_rebalance", "success": 0.88, "grounding": 0.93, "approval_rate": 0.31},
            {"workflow": "finance_ap_exception", "success": 0.91, "grounding": 0.96, "approval_rate": 0.42},
            {"workflow": "saas_incident_triage", "success": 0.84, "grounding": 0.90, "approval_rate": 0.18},
        ]
    }
