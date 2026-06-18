from pathlib import Path

import pytest
from dark_factory_governance.risk_registry import load_risk_registry
from dark_factory_skills_registry.loader import discover_skills, parse_skill_file

ROOT = Path(__file__).resolve().parents[4]


def test_discovers_all_seed_skills() -> None:
    registry = load_risk_registry(ROOT / "packages/py/governance/risk_registry.yaml")
    skills = discover_skills(ROOT / "skills", registry)

    assert {skill.manifest.name for skill in skills} == {
        "ap-exception-resolution",
        "spend-anomaly-detection",
        "promo-rebalance",
        "replenishment-control",
        "incident-triage",
        "churn-risk-investigation",
    }


def test_skill_name_must_match_parent_directory(tmp_path: Path) -> None:
    skill_dir = tmp_path / "finance" / "wrong-name"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        """---
name: other-name
description: Invalid skill.
version: 0.1.0
owner: test
risk_tier: low
required_tools:
  - policy.search
---
# Goal
Test.
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must match parent directory"):
        parse_skill_file(skill_file)
