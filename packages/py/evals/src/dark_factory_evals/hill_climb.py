from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ProposalStatus = Literal["draft", "evaluating", "ready_for_review", "rejected", "accepted"]


class TraceRecord(BaseModel):
    run_id: str
    skill_name: str
    status: str
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
    policy_citations: list[str] = Field(default_factory=list)
    outcome: dict[str, Any] | None = None
    error: str | None = None
    eval_report: dict[str, Any] | None = None


class SkillImprovementProposal(BaseModel):
    id: str
    skill_name: str
    trigger: str
    proposed_change: str
    evidence: list[str]
    diff_summary: list[str]
    eval_report_attachment: dict[str, Any] | None = None
    eval_plan: list[str]
    status: ProposalStatus
    created_at: str


class HillClimbConfig(BaseModel):
    min_repeated_events: int = Field(default=2, ge=1)
    min_task_success_rate: float = Field(default=0.8, ge=0.0, le=1.0)
    min_grounding_score: float = Field(default=0.8, ge=0.0, le=1.0)
    min_trajectory_f1: float = Field(default=0.6, ge=0.0, le=1.0)


def load_trace_corpus(path: Path) -> list[TraceRecord]:
    if not path.exists():
        raise FileNotFoundError(path)
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"{path} contains no traces")

    if path.suffix == ".jsonl":
        return [TraceRecord.model_validate_json(line) for line in raw.splitlines() if line.strip()]

    data = json.loads(raw)
    if isinstance(data, list):
        return [TraceRecord.model_validate(item) for item in data]
    if isinstance(data, dict) and isinstance(data.get("traces"), list):
        return [TraceRecord.model_validate(item) for item in data["traces"]]
    raise ValueError(f"{path} must be a JSON array, an object with traces, or JSONL")


def propose_skill_improvements(
    traces: list[TraceRecord],
    *,
    config: HillClimbConfig | None = None,
) -> list[SkillImprovementProposal]:
    cfg = config or HillClimbConfig()
    by_skill: dict[str, list[TraceRecord]] = defaultdict(list)
    for trace in traces:
        by_skill[trace.skill_name].append(trace)

    proposals: list[SkillImprovementProposal] = []
    for skill_name, skill_traces in sorted(by_skill.items()):
        proposal = _proposal_for_skill(skill_name, skill_traces, cfg)
        if proposal is not None:
            proposals.append(proposal)
    return proposals


def _proposal_for_skill(
    skill_name: str,
    traces: list[TraceRecord],
    cfg: HillClimbConfig,
) -> SkillImprovementProposal | None:
    status_counts = Counter(trace.status for trace in traces)
    gated_traces = [trace for trace in traces if trace.status == "approval_required"]
    failed_traces = [trace for trace in traces if trace.status == "failed"]

    if len(gated_traces) >= cfg.min_repeated_events:
        trigger = f"{len(gated_traces)} approval_required runs for {skill_name}"
        action = _most_common_pending_tool(gated_traces)
        proposed_change = (
            f"Update {skill_name} to gather stronger evidence before proposing {action}; "
            "add a pre-approval verification step and cite policy constraints in the ARP."
        )
        diff_summary = [
            "Add an evidence checklist before the approval gate.",
            f"Document the policy citation required before {action}.",
            "Add a golden eval case that replays the repeated approval pattern.",
        ]
    elif len(failed_traces) >= cfg.min_repeated_events:
        trigger = f"{len(failed_traces)} failed runs for {skill_name}"
        proposed_change = (
            f"Update {skill_name} recovery guidance for repeated failures; "
            "add fallback tool routing and verifier checks."
        )
        diff_summary = [
            "Add failure recovery criteria to the SKILL.md procedure.",
            "Add a verifier note for missing policy citations or failed tools.",
            "Add a golden eval case covering the failure pattern.",
        ]
    else:
        return None

    eval_report = _best_eval_report(traces)
    proposal_status = _status_from_eval(eval_report, cfg)
    evidence = _evidence_lines(traces, status_counts)

    return SkillImprovementProposal(
        id=f"sip-{uuid4().hex[:12]}",
        skill_name=skill_name,
        trigger=trigger,
        proposed_change=proposed_change,
        evidence=evidence,
        diff_summary=diff_summary,
        eval_report_attachment=eval_report,
        eval_plan=[
            f"Replay trace corpus for {skill_name}.",
            "Run existing CLEAR golden dataset for the affected vertical.",
            "Require task_success_rate and grounding_score above configured thresholds before review.",
        ],
        status=proposal_status,
        created_at=datetime.now(UTC).isoformat(),
    )


def _most_common_pending_tool(traces: list[TraceRecord]) -> str:
    tools: Counter[str] = Counter()
    for trace in traces:
        for step in trace.tool_trace:
            if step.get("requires_approval") is True and step.get("executed") is False:
                tools[str(step.get("tool_name", "gated tool"))] += 1
    if not tools:
        return "gated tool"
    return tools.most_common(1)[0][0]


def _best_eval_report(traces: list[TraceRecord]) -> dict[str, Any] | None:
    reports = [trace.eval_report for trace in traces if trace.eval_report is not None]
    if not reports:
        return None
    return reports[-1]


def _status_from_eval(eval_report: dict[str, Any] | None, cfg: HillClimbConfig) -> ProposalStatus:
    if eval_report is None:
        return "draft"
    task_success = _metric(eval_report, "task_success_rate")
    grounding = _metric(eval_report, "grounding_score")
    trajectory = _metric(eval_report, "trajectory_f1")
    if (
        task_success >= cfg.min_task_success_rate
        and grounding >= cfg.min_grounding_score
        and trajectory >= cfg.min_trajectory_f1
    ):
        return "ready_for_review"
    return "rejected"


def _metric(eval_report: dict[str, Any], name: str) -> float:
    value = eval_report.get(name, 0.0)
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _evidence_lines(traces: list[TraceRecord], status_counts: Counter[str]) -> list[str]:
    lines = [
        f"Trace corpus size: {len(traces)}",
        "Status counts: " + ", ".join(f"{status}={count}" for status, count in sorted(status_counts.items())),
    ]
    cited = sorted({citation for trace in traces for citation in trace.policy_citations})
    if cited:
        lines.append("Policy citations observed: " + ", ".join(cited))
    for trace in traces[:5]:
        pending = _most_common_pending_tool([trace])
        lines.append(f"{trace.run_id}: status={trace.status}, pending_or_gated_tool={pending}")
    return lines


def proposals_to_json(proposals: list[SkillImprovementProposal]) -> str:
    payload = {"proposals": [proposal.model_dump(mode="json") for proposal in proposals]}
    return json.dumps(payload, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SkillImprovementProposal artifacts from trace corpus JSON/JSONL."
    )
    parser.add_argument("trace_corpus", type=Path)
    parser.add_argument("--min-repeated-events", type=int, default=2)
    args = parser.parse_args()

    traces = load_trace_corpus(args.trace_corpus)
    proposals = propose_skill_improvements(
        traces,
        config=HillClimbConfig(min_repeated_events=args.min_repeated_events),
    )
    print(proposals_to_json(proposals))
