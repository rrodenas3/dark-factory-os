from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

Vertical = Literal["finance", "retail", "saas"]


class GoldenInput(BaseModel):
    description: str


class GoldenOutcome(BaseModel):
    resolved: bool
    approval_required: bool
    policy_cited: bool


class GoldenCase(BaseModel):
    id: str
    input: GoldenInput
    expected_skill: str
    expected_tools_sequence: list[str] = Field(min_length=1)
    expected_outcome: GoldenOutcome
    policy_constraints: list[str] = Field(min_length=1)


def validate_dataset(path: Path) -> list[GoldenCase]:
    cases: list[GoldenCase] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(GoldenCase.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"{path}:{line_number} is not a valid golden case: {exc}") from exc
    if not cases:
        raise ValueError(f"{path} contains no golden cases")
    return cases


def validate_all_datasets(root: Path) -> dict[str, int]:
    dataset_dir = root / "evals" / "datasets"
    results: dict[str, int] = {}
    for path in sorted(dataset_dir.glob("*_goldens.jsonl")):
        results[path.name] = len(validate_dataset(path))
    expected = {"finance_goldens.jsonl", "retail_goldens.jsonl", "saas_goldens.jsonl"}
    missing = expected.difference(results)
    if missing:
        raise ValueError(f"Missing golden datasets: {', '.join(sorted(missing))}")
    return results


def main() -> None:
    root = Path.cwd()
    results = validate_all_datasets(root)
    for name, count in results.items():
        print(f"{name}: {count} cases")
