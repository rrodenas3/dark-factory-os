from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from dark_factory_governance.risk_registry import RiskRegistry, load_risk_registry
from dark_factory_orchestration.graph import RunGraph, build_graph
from dark_factory_orchestration.state import RunState

from .metrics import CaseResult, CLEARReport, TrajectoryScore
from .validate import GoldenCase, validate_dataset


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "packages" / "py" / "governance" / "risk_registry.yaml").exists():
            return candidate
    raise FileNotFoundError("Could not find repository root containing packages/py/governance/risk_registry.yaml")


def _load_registry() -> RiskRegistry:
    registry_path = _find_repo_root(Path(__file__).resolve()) / "packages" / "py" / "governance" / "risk_registry.yaml"
    return load_risk_registry(registry_path)


class EvalRunner:
    """Runs golden eval cases through the orchestration graph and produces CLEAR metrics.

    Each case asserts:
    - trajectory: actual tool sequence ⊇ expected key tools
    - outcome: approval_required matches expected
    - grounding: at least one policy cited
    """

    def __init__(self, graph: RunGraph | None = None) -> None:
        if graph is not None:
            self._graph: RunGraph = graph
            # Registry not needed when graph is pre-built by the caller.
            self._registry: RiskRegistry | None = None
        else:
            self._registry = _load_registry()
            self._graph = build_graph(self._registry)

    def run_case(self, case: GoldenCase, vertical: str) -> CaseResult:
        initial: RunState = {
            "run_id": case.id,
            "vertical": vertical,
            "skill_name": case.expected_skill,
            "plan": [],
            "current_step": 0,
            "step_count": 0,
            "cost_usd": 0.0,
            "status": "running",
            "pending_approval": False,
            "approval_role": None,
            "tool_trace": [],
            "memory_context": [],
            "policy_citations": [],
            "outcome": None,
            "error": None,
        }

        t0 = time.monotonic()
        final = self._graph.invoke(initial)
        latency_ms = int((time.monotonic() - t0) * 1000)

        actual_tools = [t["tool_name"] for t in final.get("tool_trace", [])]
        outcome: dict[str, Any] = final.get("outcome") or {}

        trajectory = TrajectoryScore(
            case_id=case.id,
            expected=case.expected_tools_sequence,
            actual=actual_tools,
        )

        success = final.get("status") in ("completed", "approval_required")
        approval_correct = outcome.get("approval_required", False) == case.expected_outcome.approval_required
        policy_cited = bool(final.get("policy_citations")) or outcome.get("policy_cited", False)

        return CaseResult(
            case_id=case.id,
            success=success,
            approval_correct=approval_correct,
            policy_cited=policy_cited,
            trajectory=trajectory,
            latency_ms=latency_ms,
            cost_usd=final.get("cost_usd", 0.0),
        )

    def run_dataset(self, path: Path, vertical: str) -> CLEARReport:
        cases = validate_dataset(path)
        report = CLEARReport(vertical=vertical)
        for case in cases:
            result = self.run_case(case, vertical)
            report.results.append(result)
        return report


def run_all_evals(datasets_dir: Path) -> list[CLEARReport]:
    runner = EvalRunner()
    mapping = {"finance_goldens.jsonl": "finance", "retail_goldens.jsonl": "retail", "saas_goldens.jsonl": "saas"}
    reports: list[CLEARReport] = []
    for filename, vertical in mapping.items():
        path = datasets_dir / filename
        if path.exists():
            reports.append(runner.run_dataset(path, vertical))
    return reports


def main() -> None:
    root = Path.cwd()
    reports = run_all_evals(root / "evals" / "datasets")
    for report in reports:
        summary = report.summary()
        print(json.dumps(summary, indent=2))
