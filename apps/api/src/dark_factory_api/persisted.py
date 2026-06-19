from __future__ import annotations

import asyncio
import os
from typing import Any, cast
from uuid import UUID

import asyncpg
from dark_factory_memory import InMemoryStore, MemoryItem, MemoryQuery, PostgresMemoryStore, build_run_outcome_memory
from dark_factory_orchestration import RunGraph, RunState, build_graph
from dark_factory_persistence import (
    ApprovalRecord,
    ApprovalRepository,
    AuditEventRecord,
    AuditRepository,
    CostRepository,
    KnowledgeGraphRepository,
    RunRecord,
    RunRepository,
)
from dark_factory_persistence.pool import close_pool, get_pool
from dark_factory_persistence.run_ops import persist_run_result, state_from_run
from fastapi import HTTPException

from dark_factory_api.schemas import (
    ApprovalDecisionRequest,
    CreateRunRequest,
    Run,
    RunDetail,
    UCPCheckoutProposalRequest,
    UCPCheckoutProposalResponse,
    api_status,
)

_pool: asyncpg.Pool | None = None
_graph = build_graph()


def persist_runs_enabled() -> bool:
    return os.environ.get("DFOS_PERSIST_RUNS", "").lower() in {"1", "true", "yes"}


async def init_persistence() -> None:
    global _pool
    if _pool is None:
        _pool = await get_pool()
        await seed_demo_memory_persisted()


async def shutdown_persistence() -> None:
    global _pool
    if _pool is not None:
        await close_pool()
        _pool = None


def _require_pool() -> asyncpg.Pool:
    if _pool is None:
        raise HTTPException(status_code=503, detail="Database pool unavailable")
    return _pool


async def create_run_persisted(payload: CreateRunRequest) -> Run:
    repo = RunRepository(_require_pool())
    record = await repo.create_run(
        workflow_key=payload.skill_name,
        vertical=payload.vertical,
        briefing_json=dict(payload.briefing_json),
        status="pending",
    )
    await AuditRepository(_require_pool()).record(
        actor_type="user",
        event_type="run.created",
        object_type="run",
        object_id=record.id,
        payload_json={
            "workflow_key": record.workflow_key,
            "vertical": record.vertical,
            "briefing_json": record.briefing_json,
        },
    )
    return _run_from_record(record)


async def create_ucp_checkout_proposal_persisted(
    payload: UCPCheckoutProposalRequest, proposal: dict[str, object]
) -> UCPCheckoutProposalResponse:
    pool = _require_pool()
    runs = RunRepository(pool)
    approvals = ApprovalRepository(pool)

    run = await runs.get_run(payload.run_id) if payload.run_id else None
    if run is None:
        run = await runs.create_run(
            workflow_key="ucp-checkout-proposal",
            vertical="retail",
            briefing_json={
                "objective": payload.user_mandate,
                "protocol": "ucp-simulator",
                "proposal": proposal,
            },
            status="approval_required",
        )
        await runs.save_checkpoint(
            run.id,
            status="approval_required",
            checkpoint={
                "run_id": str(run.id),
                "vertical": "retail",
                "skill_name": "promo-rebalance",
                "status": "approval_required",
                "pending_approval": True,
                "approval_role": "commercial-manager",
                "pending_tool": "ucp.propose_checkout",
                "policy_citations": ["POL-PRICE-04 §1.0"],
                "tool_trace": [
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
                "outcome": {"approval_required": True, "proposal": proposal},
            },
            total_cost_usd=0.0,
            step_count=1,
            persisted_trace_len=1,
        )

    approval = await approvals.create(
        run_id=run.id,
        action_type="ucp.propose_checkout",
        action_payload=proposal,
        approver_role="commercial-manager",
        arp_json={
            "proposed_action": {
                "type": "ucp.propose_checkout",
                "description": f"Approve checkout handoff for {payload.quantity} x {payload.sku}.",
                "target_system": "ucp-simulator",
                "payload_preview": proposal,
            },
            "risk_assessment": {
                "tier": "financial",
                "reversible": False,
                "blast_radius": "single simulated retail checkout",
                "confidence": 0.89,
            },
            "policy_citations": [{"policy_id": "POL-PRICE-04", "clause_id": "1.0", "compliance_status": "pending"}],
        },
    )
    await AuditRepository(pool).record(
        actor_type="agent",
        event_type="approval.requested",
        object_type="approval",
        object_id=approval.id,
        payload_json={
            "run_id": str(run.id),
            "action_type": approval.action_type,
            "approver_role": approval.approver_role,
            "protocol": "ucp-simulator",
        },
    )
    return UCPCheckoutProposalResponse(
        approval_id=str(approval.id),
        run_id=str(run.id),
        status="pending",
        proposal=proposal,
    )


async def get_run_persisted(run_id: UUID) -> RunDetail:
    record = await RunRepository(_require_pool()).get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _detail_from_record(record)


async def list_runs_persisted() -> list[RunDetail]:
    records = await RunRepository(_require_pool()).list_runs()
    return [_detail_from_record(record) for record in records]


async def list_approvals_persisted() -> list[dict[str, object]]:
    pool = _require_pool()
    approvals = ApprovalRepository(pool)
    runs = RunRepository(pool)
    items: list[dict[str, object]] = []
    for approval in await approvals.list_pending():
        run = await runs.get_run(approval.run_id)
        items.append(_approval_to_api(approval, run))
    return items


async def decide_approval_persisted(approval_id: UUID, payload: ApprovalDecisionRequest) -> dict[str, str]:
    pool = _require_pool()
    approvals = ApprovalRepository(pool)
    runs = RunRepository(pool)

    approval = await approvals.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.decision is not None:
        raise HTTPException(status_code=409, detail="Approval already decided")

    run = await runs.get_run(approval.run_id)
    if run is None or run.checkpoint_json is None:
        raise HTTPException(status_code=409, detail="Run is not waiting for approval")

    final = await _resume_run_with_decision(
        runs,
        approvals,
        _graph,
        run,
        payload.decision,
        payload.reason,
        approval_ids=[approval.id],
    )
    await AuditRepository(pool).record(
        actor_type="user",
        event_type="approval.decided",
        object_type="approval",
        object_id=approval.id,
        payload_json={
            "run_id": str(run.id),
            "decision": payload.decision,
            "reason": payload.reason,
            "run_status": api_status(final.get("status", "failed")),
        },
    )
    return {
        "status": "accepted",
        "decision": payload.decision,
        "run_status": api_status(final.get("status", "failed")),
        "run_id": str(run.id),
    }


async def resume_run_persisted(run_id: UUID, payload: ApprovalDecisionRequest) -> dict[str, str]:
    pool = _require_pool()
    runs = RunRepository(pool)
    approvals = ApprovalRepository(pool)
    record = await runs.get_run(run_id)
    if record is None or record.checkpoint_json is None:
        raise HTTPException(status_code=404, detail="Run not found or not resumable")

    final = await _resume_run_with_decision(
        runs,
        approvals,
        _graph,
        record,
        payload.decision,
        payload.reason,
    )
    await AuditRepository(pool).record(
        actor_type="user",
        event_type="run.resumed",
        object_type="run",
        object_id=record.id,
        payload_json={
            "decision": payload.decision,
            "reason": payload.reason,
            "run_status": api_status(final.get("status", "failed")),
        },
    )
    return {"status": "accepted", "run_status": api_status(final.get("status", "failed"))}


async def list_audit_events_persisted(
    *,
    run_id: UUID | None = None,
    event_type: str | None = None,
) -> list[dict[str, object]]:
    events = await AuditRepository(_require_pool()).list_events(run_id=run_id, event_type=event_type)
    return [_audit_event_to_api(event) for event in events]


async def cost_summary_persisted() -> dict[str, object]:
    return await CostRepository(_require_pool()).summary()


async def knowledge_graph_persisted() -> dict[str, object]:
    graph = await KnowledgeGraphRepository(_require_pool()).graph()
    if graph["nodes"]:
        return graph
    return await seed_demo_knowledge_graph_persisted()


async def seed_demo_knowledge_graph_persisted() -> dict[str, object]:
    repo = KnowledgeGraphRepository(_require_pool())
    vendor = await repo.upsert_entity(
        entity_type="vendor",
        entity_key="contoso-logistics",
        props_json={"label": "Contoso Logistics", "vertical": "finance", "risk": "elevated"},
    )
    sku = await repo.upsert_entity(
        entity_type="sku",
        entity_key="sparkling-water-12pk",
        props_json={"label": "Sparkling Water 12pk", "vertical": "retail", "risk": "medium"},
    )
    billing_api = await repo.upsert_entity(
        entity_type="service",
        entity_key="billing-api",
        props_json={"label": "billing-api", "vertical": "saas", "risk": "high"},
    )
    price_policy = await repo.upsert_entity(
        entity_type="policy",
        entity_key="pol-price-04",
        props_json={"label": "POL-PRICE-04", "vertical": "retail", "risk": "control"},
    )
    ap_policy = await repo.upsert_entity(
        entity_type="policy",
        entity_key="pol-ap-12",
        props_json={"label": "POL-AP-12", "vertical": "finance", "risk": "control"},
    )
    await repo.create_edge(
        source_entity_id=vendor.id,
        relation="requires_policy_review",
        target_entity_id=ap_policy.id,
        props_json={"evidence": "Amount mismatches above threshold."},
    )
    await repo.create_edge(
        source_entity_id=sku.id,
        relation="constrained_by",
        target_entity_id=price_policy.id,
        props_json={"evidence": "Price band changes must remain within baseline limits."},
    )
    await repo.create_edge(
        source_entity_id=billing_api.id,
        relation="shares_failure_pattern",
        target_entity_id=vendor.id,
        props_json={"evidence": "Invoice preview and payment retry incidents affect AP exception flow."},
    )
    return await repo.graph()


async def get_trace_persisted(run_id: UUID) -> dict[str, object]:
    detail = await get_run_persisted(run_id)
    return {
        "run_id": str(detail.id),
        "status": detail.status,
        "tool_trace": detail.tool_trace,
        "policy_citations": detail.policy_citations,
        "outcome": detail.outcome,
    }


async def search_memory_persisted(query: MemoryQuery) -> list[dict[str, object]]:
    store = PostgresMemoryStore(_require_pool())
    results = await store.search(query)
    return [_memory_result_to_api(result.item, round(result.score, 4)) for result in results]


async def memory_demo_persisted() -> list[dict[str, object]]:
    store = PostgresMemoryStore(_require_pool())
    return [_memory_item_to_api(item) for item in await store.all()]


async def seed_demo_memory_persisted() -> None:
    store = PostgresMemoryStore(_require_pool())
    demo = InMemoryStore()
    demo.seed_demo()
    for item in demo.all():
        await store.upsert(item, validate=False)


async def write_run_outcome_memory(state: dict[str, Any]) -> None:
    item = build_run_outcome_memory(state)
    if item is None:
        return
    store = PostgresMemoryStore(_require_pool())
    try:
        await store.upsert(item)
    except ValueError as exc:
        if "append-only" not in str(exc):
            raise


async def _resume_run_with_decision(
    runs: RunRepository,
    approvals: ApprovalRepository,
    graph: RunGraph,
    run: RunRecord,
    decision: str,
    reason: str,
    *,
    approval_ids: list[UUID] | None = None,
) -> RunState:
    targets = approval_ids
    if targets is None:
        pending = await approvals.list_pending_for_run(run.id)
        targets = [item.id for item in pending]

    for approval_id in targets:
        await approvals.decide(
            approval_id,
            decision=cast(Any, "approved" if decision == "approved" else "rejected"),
            reason=reason,
        )

    state = cast(RunState, state_from_run(run))
    final = await asyncio.to_thread(graph.resume, state, decision)
    outcome = {
        **(final.get("outcome") or {}),
        "approval_decision": decision,
        "decision_reason": reason,
    }
    final = {**final, "outcome": outcome}
    await persist_run_result(runs, approvals, run, dict(final))
    await write_run_outcome_memory(dict(final))
    return final


def _approval_to_api(approval: ApprovalRecord, run: RunRecord | None) -> dict[str, object]:
    checkpoint = (run.checkpoint_json or {}) if run else {}
    arp = approval.arp_json or {}
    policy_citations = arp.get("policy_citations", [])
    citations = [
        f"{item.get('policy_id')} §{item.get('clause_id')}"
        for item in policy_citations
        if isinstance(item, dict)
    ] or list(checkpoint.get("policy_citations", []))
    tool_trace = list(checkpoint.get("tool_trace", []))
    risk = arp.get("risk_assessment", {})
    risk_tier = str(risk.get("tier") or "financial") if isinstance(risk, dict) else "financial"
    for step in reversed(tool_trace):
        if step.get("tool_name") == approval.action_type:
            risk_tier = str(risk_tier or step.get("risk_tier") or "financial")
            break

    briefing = (run.briefing_json or {}) if run else {}
    proposed = arp.get("proposed_action", {})
    summary = str(
        proposed.get("description") if isinstance(proposed, dict) else ""
    ) or str(briefing.get("objective") or f"Approve {approval.action_type} for run {approval.run_id}")
    evidence_items = arp.get("evidence", [])
    evidence = [
        str(item.get("citation"))
        for item in evidence_items
        if isinstance(item, dict) and item.get("citation")
    ] or citations

    return {
        "id": str(approval.id),
        "run_id": str(approval.run_id),
        "action_type": approval.action_type,
        "approver_role": approval.approver_role,
        "risk_tier": risk_tier,
        "status": "pending",
        "summary": summary,
        "evidence": evidence,
        "arp_json": arp,
    }


def _run_from_record(record: RunRecord) -> Run:
    return Run(
        id=record.id,
        workflow_key=record.workflow_key,
        status=record.status,
        vertical=record.vertical or "finance",
        total_cost_usd=record.total_cost_usd,
        step_count=record.step_count,
    )


def _audit_event_to_api(event: AuditEventRecord) -> dict[str, object]:
    return {
        "id": str(event.id),
        "actor_type": event.actor_type,
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "event_type": event.event_type,
        "object_type": event.object_type,
        "object_id": str(event.object_id) if event.object_id else None,
        "payload_json": event.payload_json,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def _detail_from_record(record: RunRecord) -> RunDetail:
    checkpoint = record.checkpoint_json or {}
    return RunDetail(
        id=record.id,
        workflow_key=record.workflow_key,
        status=record.status,
        vertical=record.vertical or "finance",
        total_cost_usd=record.total_cost_usd,
        step_count=record.step_count,
        skill_name=record.workflow_key,
        pending_approval=bool(checkpoint.get("pending_approval", record.status == "approval_required")),
        approval_role=checkpoint.get("approval_role"),
        policy_citations=list(checkpoint.get("policy_citations", [])),
        tool_trace=list(checkpoint.get("tool_trace", [])),
        outcome=checkpoint.get("outcome"),
        error=checkpoint.get("error"),
    )


def _memory_result_to_api(item: MemoryItem, score: float) -> dict[str, object]:
    return {
        "entity_key": item.entity_key,
        "memory_type": item.memory_type,
        "score": score,
        "source_trust": item.source_trust,
        "content": item.content,
    }


def _memory_item_to_api(item: MemoryItem) -> dict[str, object]:
    return {
        "namespace": item.namespace,
        "entity_key": item.entity_key,
        "memory_type": item.memory_type,
        "trust": item.source_trust,
        "decay_score": item.decay_score,
        "summary": item.content.get("summary", ""),
    }
