from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from dark_factory_evals.hill_climb import HillClimbConfig, load_trace_corpus, propose_skill_improvements
from dark_factory_evals.runner import run_all_evals
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/evals", tags=["evals"])

_RUN_LOCK = Lock()
_LATEST_SUMMARY: dict[str, Any] | None = None


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "evals" / "datasets").exists():
            return candidate
    raise FileNotFoundError("Could not find repository root containing evals/datasets")


def _run_live_evals() -> dict[str, Any]:
    root = _find_repo_root(Path(__file__).resolve())
    reports = run_all_evals(root / "evals" / "datasets")
    generated_at = datetime.now(UTC).isoformat()
    metrics = [_metric_from_summary(report.summary()) for report in reports]
    return {
        "status": "completed",
        "source": "eval_runner",
        "generated_at": generated_at,
        "metrics": metrics,
        "totals": _totals(metrics),
    }


def _run_skill_improvement_scan() -> dict[str, Any]:
    root = _find_repo_root(Path(__file__).resolve())
    corpus_path = root / "evals" / "trace_corpus" / "skill_improvement_traces.jsonl"
    traces = load_trace_corpus(corpus_path)
    proposals = propose_skill_improvements(traces, config=HillClimbConfig(min_repeated_events=2))
    return {
        "status": "completed",
        "source": "trace_corpus",
        "generated_at": datetime.now(UTC).isoformat(),
        "trace_count": len(traces),
        "proposal_count": len(proposals),
        "proposals": [proposal.model_dump(mode="json") for proposal in proposals],
    }


def _metric_from_summary(summary: dict[str, object]) -> dict[str, object]:
    vertical = str(summary["vertical"])
    trajectory_f1 = _as_float(summary["trajectory_f1"])
    task_success_rate = _as_float(summary["task_success_rate"])
    approval_precision = _as_float(summary["approval_precision"])
    return {
        "workflow": f"{vertical}_goldens",
        "vertical": vertical,
        "cases": _as_int(summary["cases"]),
        "task_success_rate": task_success_rate,
        "grounding_score": _as_float(summary["grounding_score"]),
        "approval_precision": approval_precision,
        "trajectory_f1": trajectory_f1,
        "avg_cost_usd": _as_float(summary["avg_cost_usd"]),
        "p95_latency_ms": _as_float(summary["p95_latency_ms"]),
        "efficiency_score": round(trajectory_f1, 3),
        "reliability_score": round((task_success_rate + approval_precision) / 2, 3),
    }


def _totals(metrics: list[dict[str, object]]) -> dict[str, object]:
    if not metrics:
        return {
            "cases": 0,
            "task_success_rate": 0.0,
            "grounding_score": 0.0,
            "trajectory_f1": 0.0,
            "avg_cost_usd": 0.0,
            "p95_latency_ms": 0.0,
        }

    count = len(metrics)
    return {
        "cases": sum(_as_int(metric["cases"]) for metric in metrics),
        "task_success_rate": round(sum(_as_float(metric["task_success_rate"]) for metric in metrics) / count, 3),
        "grounding_score": round(sum(_as_float(metric["grounding_score"]) for metric in metrics) / count, 3),
        "trajectory_f1": round(sum(_as_float(metric["trajectory_f1"]) for metric in metrics) / count, 3),
        "avg_cost_usd": round(sum(_as_float(metric["avg_cost_usd"]) for metric in metrics) / count, 4),
        "p95_latency_ms": max(_as_float(metric["p95_latency_ms"]) for metric in metrics),
    }


def _as_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value).__name__}")


def _as_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float | str):
        return int(value)
    raise TypeError(f"Expected integer value, got {type(value).__name__}")


@router.get("/demo")
def get_eval_summary() -> dict[str, Any]:
    global _LATEST_SUMMARY
    if _LATEST_SUMMARY is None:
        _LATEST_SUMMARY = _run_live_evals()
    return _LATEST_SUMMARY


@router.post("/run", status_code=202)
def run_eval_summary() -> dict[str, Any]:
    global _LATEST_SUMMARY
    if not _RUN_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Eval run already in progress")
    try:
        _LATEST_SUMMARY = _run_live_evals()
        return _LATEST_SUMMARY
    finally:
        _RUN_LOCK.release()


@router.get("/skill-improvements")
def get_skill_improvement_proposals() -> dict[str, Any]:
    return _run_skill_improvement_scan()
