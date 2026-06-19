import json
from pathlib import Path

from dark_factory_artifacts.validate import validate_all_schemas
from dark_factory_evals.validate import validate_all_datasets
from dark_factory_governance.risk_registry import load_risk_registry
from dark_factory_skills_registry.loader import discover_skills

ROOT = Path(__file__).resolve().parents[1]


def test_artifact_schemas_are_valid() -> None:
    assert len(validate_all_schemas(ROOT)) >= 4


def test_golden_datasets_are_valid() -> None:
    results = validate_all_datasets(ROOT)
    assert results["finance_goldens.jsonl"] == 10
    assert results["retail_goldens.jsonl"] == 5
    assert results["saas_goldens.jsonl"] == 5


def test_all_seed_skills_reference_known_tools() -> None:
    registry = load_risk_registry(ROOT / "packages/py/governance/risk_registry.yaml")
    skills = discover_skills(ROOT / "skills", registry)
    assert len(skills) == 6


def test_golden_datasets_reference_known_skills_and_tools() -> None:
    registry = load_risk_registry(ROOT / "packages/py/governance/risk_registry.yaml")
    skills = discover_skills(ROOT / "skills", registry)
    skill_names = {skill.manifest.name for skill in skills}

    for dataset_path in sorted((ROOT / "evals" / "datasets").glob("*_goldens.jsonl")):
        for line_number, line in enumerate(dataset_path.read_text(encoding="utf-8").splitlines(), start=1):
            record = json.loads(line)
            expected_skill = record["expected_skill"]
            assert expected_skill in skill_names, f"{dataset_path.name}:{line_number} unknown skill {expected_skill}"

            for tool_name in record["expected_tools_sequence"]:
                registry.require_tool(tool_name)
