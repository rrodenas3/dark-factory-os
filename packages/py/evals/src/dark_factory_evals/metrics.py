from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean


@dataclass
class TrajectoryScore:
    case_id: str
    expected: list[str]
    actual: list[str]

    @property
    def precision(self) -> float:
        if not self.actual:
            return 0.0
        hits = sum(1 for t in self.actual if t in self.expected)
        return hits / len(self.actual)

    @property
    def recall(self) -> float:
        if not self.expected:
            return 1.0
        hits = sum(1 for t in self.expected if t in self.actual)
        return hits / len(self.expected)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * p * r / (p + r)

    @property
    def order_correct(self) -> bool:
        expected_filtered = [t for t in self.expected if t in self.actual]
        actual_filtered = [t for t in self.actual if t in self.expected]
        return expected_filtered == actual_filtered


@dataclass
class CaseResult:
    case_id: str
    success: bool
    approval_correct: bool
    policy_cited: bool
    trajectory: TrajectoryScore
    latency_ms: int
    cost_usd: float

    @property
    def grounding_score(self) -> float:
        return 1.0 if self.policy_cited else 0.0


@dataclass
class CLEARReport:
    vertical: str
    results: list[CaseResult] = field(default_factory=list)

    @property
    def task_success_rate(self) -> float:
        if not self.results:
            return 0.0
        return mean(1.0 if r.success else 0.0 for r in self.results)

    @property
    def grounding_score(self) -> float:
        if not self.results:
            return 0.0
        return mean(r.grounding_score for r in self.results)

    @property
    def approval_precision(self) -> float:
        if not self.results:
            return 0.0
        return mean(1.0 if r.approval_correct else 0.0 for r in self.results)

    @property
    def trajectory_f1(self) -> float:
        if not self.results:
            return 0.0
        return mean(r.trajectory.f1 for r in self.results)

    @property
    def avg_cost_usd(self) -> float:
        if not self.results:
            return 0.0
        return mean(r.cost_usd for r in self.results)

    @property
    def p95_latency_ms(self) -> float:
        if not self.results:
            return 0.0
        sorted_lat = sorted(r.latency_ms for r in self.results)
        idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        return float(sorted_lat[idx])

    def summary(self) -> dict[str, object]:
        return {
            "vertical": self.vertical,
            "cases": len(self.results),
            "task_success_rate": round(self.task_success_rate, 3),
            "grounding_score": round(self.grounding_score, 3),
            "approval_precision": round(self.approval_precision, 3),
            "trajectory_f1": round(self.trajectory_f1, 3),
            "avg_cost_usd": round(self.avg_cost_usd, 4),
            "p95_latency_ms": round(self.p95_latency_ms, 1),
        }
