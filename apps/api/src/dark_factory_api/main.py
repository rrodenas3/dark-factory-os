from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from dark_factory_memory import InMemoryStore, MemoryQuery
from dark_factory_orchestration import RunState, build_graph
from dark_factory_tool_adapters import MCP_PROTOCOL_VERSION, tool_endpoints
from dark_factory_tool_adapters.ucp_simulator import propose_checkout
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from dark_factory_api import persisted
from dark_factory_api.evals import router as evals_router
from dark_factory_api.schemas import (
    AgentIdentity,
    ApprovalDecisionRequest,
    CreateRunRequest,
    HealthResponse,
    MemorySearchRequest,
    Run,
    RunDetail,
    UCPCheckoutProposalRequest,
    UCPCheckoutProposalResponse,
    UserContext,
    WorkbenchFocus,
    api_status,
)

RUNS: dict[UUID, RunDetail] = {}
RUN_STATES: dict[UUID, RunState] = {}
RUN_GRAPH = build_graph()
MEMORY_STORE = InMemoryStore()
MEMORY_STORE.seed_demo()

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
    {"name": "ap-exception-resolution", "vertical": "finance", "risk_tier": "medium", "eval_status": "passing"},
    {"name": "spend-anomaly-detection", "vertical": "finance", "risk_tier": "medium", "eval_status": "passing"},
    {"name": "promo-rebalance", "vertical": "retail", "risk_tier": "medium", "eval_status": "passing"},
    {"name": "replenishment-control", "vertical": "retail", "risk_tier": "medium", "eval_status": "passing"},
    {"name": "incident-triage", "vertical": "saas", "risk_tier": "medium", "eval_status": "passing"},
    {"name": "churn-risk-investigation", "vertical": "saas", "risk_tier": "medium", "eval_status": "passing"},
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

DEMO_AUDIT_EVENTS: list[dict[str, object]] = [
    {
        "id": "audit-demo-001",
        "actor_type": "agent",
        "actor_id": None,
        "event_type": "approval.requested",
        "object_type": "approval",
        "object_id": "apr-fin-001",
        "payload_json": {"run_id": "demo-finance-ap", "action_type": "erp.post_payment"},
        "created_at": "2026-06-19T00:00:00Z",
    },
    {
        "id": "audit-demo-002",
        "actor_type": "user",
        "actor_id": None,
        "event_type": "run.created",
        "object_type": "run",
        "object_id": "demo-retail-promo",
        "payload_json": {"workflow_key": "promo-rebalance", "vertical": "retail"},
        "created_at": "2026-06-19T00:01:00Z",
    },
]

DEMO_USER_CONTEXT = UserContext(
    id="user-demo-ai-lead",
    email="ai-lead@darkfactory.local",
    role="admin",
    verticals=["finance", "retail", "saas"],
    permissions=[
        "runs:write",
        "approvals:write",
        "memory:read",
        "skills:review",
        "audit:read",
        "costs:read",
    ],
    active_agent=AgentIdentity(
        id="agent-supervisor-001",
        name="Enterprise Operations Supervisor",
        risk_tier="high",
        budget_daily_usd=10.0,
        status="active",
    ),
    workbench=[
        WorkbenchFocus(
            id="finance-ap-exception",
            label="AP exception control",
            vertical="finance",
            priority="critical",
            signal="Amount mismatch over policy threshold with pending ARP.",
            next_action="Review evidence bundle and decide payment gate.",
            href="/approvals",
        ),
        WorkbenchFocus(
            id="retail-margin-rebalance",
            label="Promo margin rebalance",
            vertical="retail",
            priority="high",
            signal="Campaign margin drift plus stock availability supports price-band proposal.",
            next_action="Inspect WebMCP/UCP proposal before commercial approval.",
            href="/retail/promo-confirm",
        ),
        WorkbenchFocus(
            id="saas-incident-followup",
            label="Incident follow-up loop",
            vertical="saas",
            priority="medium",
            signal="Billing API spike needs correlation with churn-risk accounts.",
            next_action="Open trace timeline and verify remediation steps.",
            href="/traces",
        ),
    ],
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if persisted.persist_runs_enabled():
        await persisted.init_persistence()
    try:
        yield
    finally:
        if persisted.persist_runs_enabled():
            await persisted.shutdown_persistence()


app = FastAPI(
    title="Dark Factory OS Control Plane API",
    version="0.1.0",
    description="Governed agentic operations platform API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evals_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="dark-factory-api", timestamp=datetime.now(UTC))


@app.get("/.well-known/agent-card.json")
def agent_card() -> JSONResponse:
    card_path = Path(__file__).resolve().parents[2] / ".well-known" / "agent-card.json"
    return JSONResponse(json.loads(card_path.read_text(encoding="utf-8")))


@app.get("/api/runs", response_model=list[Run])
async def list_runs() -> list[RunDetail]:
    if persisted.persist_runs_enabled():
        return await persisted.list_runs_persisted()
    return list(RUNS.values())


@app.get("/api/demo/runs")
def list_demo_runs() -> list[dict[str, object]]:
    return DEMO_RUNS


@app.get("/api/me", response_model=UserContext)
def get_user_context() -> UserContext:
    return DEMO_USER_CONTEXT


@app.post("/api/runs", response_model=Run)
async def create_run(payload: CreateRunRequest, response: Response) -> Run:
    if persisted.persist_runs_enabled():
        run = await persisted.create_run_persisted(payload)
        response.status_code = 202
        return run
    response.status_code = 201
    return _create_run_memory(payload)


def _create_run_memory(payload: CreateRunRequest) -> RunDetail:
    run_id = uuid4()
    state = RUN_GRAPH.invoke(
        RunState(
            run_id=str(run_id),
            vertical=payload.vertical,
            skill_name=payload.skill_name,
            outcome={"briefing": payload.briefing_json},
        )
    )
    run = RunDetail(
        id=run_id,
        workflow_key=payload.skill_name,
        status=api_status(state.get("status", "failed")),
        vertical=payload.vertical,
        total_cost_usd=state.get("cost_usd", 0.0),
        step_count=state.get("step_count", 0),
        skill_name=payload.skill_name,
        pending_approval=state.get("pending_approval", False),
        approval_role=state.get("approval_role"),
        policy_citations=state.get("policy_citations", []),
        tool_trace=state.get("tool_trace", []),
        outcome=state.get("outcome"),
        error=state.get("error"),
    )
    RUNS[run.id] = run
    RUN_STATES[run.id] = state
    return run


@app.get("/api/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: UUID) -> RunDetail:
    if persisted.persist_runs_enabled():
        return await persisted.get_run_persisted(run_id)
    try:
        return RUNS[run_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/runs/{run_id}/resume", status_code=202)
async def resume_run(run_id: UUID, payload: ApprovalDecisionRequest) -> dict[str, str]:
    if persisted.persist_runs_enabled():
        return await persisted.resume_run_persisted(run_id, payload)

    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found")
    run = RUNS[run_id]
    state = RUN_STATES.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run state not found")

    resumed = RUN_GRAPH.resume(state, payload.decision)
    outcome = {
        **(resumed.get("outcome") or run.outcome or {}),
        "approval_decision": payload.decision,
        "decision_reason": payload.reason,
    }
    RUNS[run_id] = run.model_copy(
        update={
            "status": api_status(resumed.get("status", "failed")),
            "total_cost_usd": resumed.get("cost_usd", run.total_cost_usd),
            "step_count": resumed.get("step_count", run.step_count),
            "pending_approval": resumed.get("pending_approval", False),
            "approval_role": resumed.get("approval_role"),
            "policy_citations": resumed.get("policy_citations", run.policy_citations),
            "tool_trace": resumed.get("tool_trace", run.tool_trace),
            "outcome": outcome,
            "error": resumed.get("error"),
        }
    )
    resumed["outcome"] = outcome
    RUN_STATES[run_id] = resumed
    return {"status": "accepted", "run_status": RUNS[run_id].status}


@app.get("/api/runs/{run_id}/trace")
async def get_run_trace(run_id: UUID) -> dict[str, object]:
    if persisted.persist_runs_enabled():
        return await persisted.get_trace_persisted(run_id)
    try:
        run = RUNS[run_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return {
        "run_id": str(run.id),
        "status": run.status,
        "tool_trace": run.tool_trace,
        "policy_citations": run.policy_citations,
        "outcome": run.outcome,
    }


@app.get("/api/skills")
def list_skills() -> list[dict[str, str]]:
    return DEMO_SKILLS


@app.get("/api/tools/catalog")
def tools_catalog() -> dict[str, object]:
    endpoints = [endpoint.model_dump(mode="json") for endpoint in tool_endpoints()]
    return {
        "protocol": "mcp",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "streamable-http-stateless",
        "endpoint_count": len(endpoints),
        "endpoints": endpoints,
    }


@app.get("/api/approvals")
async def list_approvals() -> list[dict[str, object]]:
    if persisted.persist_runs_enabled():
        return await persisted.list_approvals_persisted()
    return DEMO_APPROVALS


@app.post("/api/approvals/{approval_id}/decision", status_code=202)
async def decide_approval(approval_id: str, payload: ApprovalDecisionRequest) -> dict[str, str]:
    if persisted.persist_runs_enabled():
        try:
            return await persisted.decide_approval_persisted(UUID(approval_id), payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Approval not found") from exc
    if approval_id not in {approval["id"] for approval in DEMO_APPROVALS}:
        raise HTTPException(status_code=404, detail="Approval not found")
    DEMO_AUDIT_EVENTS.insert(
        0,
        {
            "id": f"audit-{uuid4().hex[:8]}",
            "actor_type": "user",
            "actor_id": None,
            "event_type": "approval.decided",
            "object_type": "approval",
            "object_id": approval_id,
            "payload_json": {"decision": payload.decision, "reason": payload.reason},
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    return {"status": "accepted", "decision": payload.decision}


@app.get("/api/audit/events")
async def list_audit_events(run_id: UUID | None = None, event_type: str | None = None) -> list[dict[str, object]]:
    if persisted.persist_runs_enabled():
        return await persisted.list_audit_events_persisted(run_id=run_id, event_type=event_type)

    items = DEMO_AUDIT_EVENTS
    if run_id is not None:
        items = [item for item in items if item.get("object_id") == str(run_id)]
    if event_type is not None:
        items = [item for item in items if item.get("event_type") == event_type]
    return items


def _sse_event(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@app.get("/api/events")
async def stream_events(run_id: UUID | None = None, once: bool = False) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        events = await list_audit_events(run_id=run_id)
        for item in events[:10]:
            yield _sse_event(str(item["event_type"]), item)
        yield _sse_event(
            "control_plane.heartbeat",
            {
                "id": f"heartbeat-{uuid4().hex[:8]}",
                "actor_type": "system",
                "event_type": "control_plane.heartbeat",
                "payload_json": {"live": True, "source": "api-events"},
                "created_at": datetime.now(UTC).isoformat(),
            },
        )
        if once:
            return
        while True:
            await asyncio.sleep(15)
            yield _sse_event(
                "control_plane.heartbeat",
                {
                    "id": f"heartbeat-{uuid4().hex[:8]}",
                    "actor_type": "system",
                    "event_type": "control_plane.heartbeat",
                    "payload_json": {"live": True, "source": "api-events"},
                    "created_at": datetime.now(UTC).isoformat(),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.post("/api/memory/search")
async def search_memory(payload: MemorySearchRequest) -> dict[str, object]:
    """Query governed memory with SSGM-style decay-weighted retrieval."""
    q = MemoryQuery(
        query=payload.query,
        namespace=payload.namespace,
        memory_type=payload.memory_type,
        k=payload.k,
        decay_weighted=payload.decay_weighted,
        min_trust=payload.min_trust,
    )
    if persisted.persist_runs_enabled():
        matches = await persisted.search_memory_persisted(q)
        return {"query": payload.query, "namespace": payload.namespace, "matches": matches}

    results = MEMORY_STORE.search(q)
    return {
        "query": payload.query,
        "namespace": payload.namespace,
        "matches": [
            {
                "entity_key": r.item.entity_key,
                "memory_type": r.item.memory_type,
                "score": round(r.score, 4),
                "source_trust": r.item.source_trust,
                "content": r.item.content,
            }
            for r in results
        ],
    }


@app.get("/api/memory/demo")
async def memory_demo() -> list[dict[str, object]]:
    if persisted.persist_runs_enabled():
        return await persisted.memory_demo_persisted()

    return [
        {
            "namespace": item.namespace,
            "entity_key": item.entity_key,
            "memory_type": item.memory_type,
            "trust": item.source_trust,
            "decay_score": item.decay_score,
            "summary": item.content.get("summary", ""),
        }
        for item in MEMORY_STORE.all()
    ]


@app.get("/api/knowledge/graph")
def knowledge_graph_demo() -> dict[str, object]:
    nodes = [
        {
            "id": "contoso-logistics",
            "label": "Contoso Logistics",
            "type": "vendor",
            "vertical": "finance",
            "risk": "elevated",
        },
        {
            "id": "sparkling-water-12pk",
            "label": "Sparkling Water 12pk",
            "type": "sku",
            "vertical": "retail",
            "risk": "medium",
        },
        {
            "id": "billing-api",
            "label": "billing-api",
            "type": "service",
            "vertical": "saas",
            "risk": "high",
        },
        {"id": "pol-price-04", "label": "POL-PRICE-04", "type": "policy", "vertical": "retail", "risk": "control"},
        {"id": "pol-ap-12", "label": "POL-AP-12", "type": "policy", "vertical": "finance", "risk": "control"},
    ]
    edges = [
        {
            "source": "contoso-logistics",
            "relation": "requires_policy_review",
            "target": "pol-ap-12",
            "evidence": "Amount mismatches above threshold.",
        },
        {
            "source": "sparkling-water-12pk",
            "relation": "constrained_by",
            "target": "pol-price-04",
            "evidence": "Price band changes must remain within baseline limits.",
        },
        {
            "source": "billing-api",
            "relation": "shares_failure_pattern",
            "target": "contoso-logistics",
            "evidence": "Invoice preview and payment retry incidents affect AP exception flow.",
        },
    ]
    return {"nodes": nodes, "edges": edges, "generated_from": "seeded_memory"}


@app.post("/api/ucp/checkout-proposals", response_model=UCPCheckoutProposalResponse, status_code=202)
async def create_ucp_checkout_proposal(payload: UCPCheckoutProposalRequest) -> UCPCheckoutProposalResponse:
    proposal = propose_checkout(payload.model_dump(exclude_none=True))
    if persisted.persist_runs_enabled():
        return await persisted.create_ucp_checkout_proposal_persisted(payload, proposal)
    return _create_ucp_checkout_proposal_memory(payload, proposal)


def _create_ucp_checkout_proposal_memory(
    payload: UCPCheckoutProposalRequest, proposal: dict[str, object]
) -> UCPCheckoutProposalResponse:
    run_id = payload.run_id or uuid4()
    if run_id not in RUNS:
        run = RunDetail(
            id=run_id,
            workflow_key="ucp-checkout-proposal",
            status="approval_required",
            vertical="retail",
            total_cost_usd=0.0,
            step_count=1,
            skill_name="promo-rebalance",
            pending_approval=True,
            approval_role="commercial-manager",
            policy_citations=["POL-PRICE-04 §1.0"],
            tool_trace=[
                {
                    "tool_name": "ucp.propose_checkout",
                    "risk_tier": "financial",
                    "success": True,
                    "latency_ms": 0,
                    "cost_usd": 0.0,
                    "requires_approval": True,
                    "executed": False,
                    "proposal": proposal,
                }
            ],
            outcome={"approval_required": True, "proposal": proposal},
        )
        RUNS[run_id] = run
    approval_id = f"ucp-{uuid4().hex[:8]}"
    DEMO_APPROVALS.append(
        {
            "id": approval_id,
            "run_id": str(run_id),
            "action_type": "ucp.propose_checkout",
            "approver_role": "commercial-manager",
            "risk_tier": "financial",
            "status": "pending",
            "summary": f"Approve UCP checkout proposal for {payload.quantity} x {payload.sku}.",
            "evidence": ["POL-PRICE-04", "UCP-SIMULATOR", str(proposal["cart_id"])],
        }
    )
    return UCPCheckoutProposalResponse(
        approval_id=approval_id,
        run_id=str(run_id),
        status="pending",
        proposal=proposal,
    )


@app.get("/api/costs/summary")
async def cost_summary() -> dict[str, object]:
    if persisted.persist_runs_enabled():
        return await persisted.cost_summary_persisted()

    return {
        "total_usd": 0.84,
        "by_category": {"model_tokens": 0.55, "retrieval": 0.09, "tool_compute": 0.11, "human_review": 0.09},
        "by_vertical": {"finance": 0.29, "retail": 0.34, "saas": 0.21},
        "clear": {
            "cost": 0.84,
            "latency": {"p50_seconds": 8.5, "p95_seconds": 14.8},
            "efficiency": {"tokens_per_successful_step": 0, "successful_steps": 21},
            "accuracy": {"task_success_rate": 0.88},
            "reliability": {"tool_success_rate": 0.94},
        },
    }


