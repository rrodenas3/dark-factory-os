import json
from pathlib import Path

import yaml
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


def test_openapi_matches_control_plane_manifest() -> None:
    spec = yaml.safe_load((ROOT / "apps" / "api" / "openapi.yaml").read_text(encoding="utf-8"))
    api_paths = [path for path in spec["paths"] if path.startswith("/api/")]

    assert spec["openapi"] == "3.1.0"
    assert len(api_paths) == 16
    assert spec["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"
    assert {"approval.requested", "approval.decided"} <= set(spec["webhooks"])

    required_paths = {
        "/api/runs",
        "/api/runs/{id}/resume",
        "/api/approvals/{id}/decision",
        "/api/memory/search",
        "/api/costs/summary",
    }
    assert required_paths <= set(spec["paths"])

    schemas = spec["components"]["schemas"]
    for schema_name in ["Run", "Approval", "ActionReadinessPack", "MemorySearchRequest", "CostSummary", "Error"]:
        assert schema_name in schemas

    assert schemas["Vertical"]["enum"] == ["retail", "finance", "saas"]
    assert schemas["RunStatus"]["enum"] == [
        "pending",
        "running",
        "paused",
        "approval_required",
        "completed",
        "failed",
        "cancelled",
    ]


def test_agent_card_matches_a2a_manifest() -> None:
    card = json.loads((ROOT / "apps" / "api" / ".well-known" / "agent-card.json").read_text(encoding="utf-8"))

    assert card["schemaVersion"] == "1.0"
    assert card["name"] == "dark-factory-os"
    assert card["url"] != "https://your-deployment.example.com"
    assert set(card["protocolBindings"]) == {"json-rpc", "http"}

    skill_ids = {skill["id"] for skill in card["skills"]}
    assert skill_ids == {"retail-ops", "finance-ops", "saas-ops"}

    assert card["security"] == {"scheme": "Bearer", "scopes": ["runs:write", "approvals:write", "memory:read"]}
    assert card["governance"]["humanGateRequired"] == ["destructive", "financial"]
    assert card["governance"]["auditTrail"] is True
    assert card["governance"]["riskTiers"] == ["read_only", "financial", "destructive"]


def test_env_example_contains_required_local_stack_variables() -> None:
    env_lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    env_keys = {line.split("=", 1)[0] for line in env_lines if line and not line.startswith("#")}

    required_keys = {
        "DATABASE_URL",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "REDIS_URL",
        "TEMPORAL_HOST",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "LANGSMITH_API_KEY",
        "JWT_SECRET",
        "NEXT_PUBLIC_API_URL",
    }
    assert required_keys <= env_keys


def test_docker_compose_matches_local_stack_manifest() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    required_services = {
        "postgres",
        "redis",
        "temporal",
        "temporal-ui",
        "api",
        "worker",
        "web",
        "otel-collector",
        "jaeger",
    }
    assert required_services <= set(services)

    assert services["postgres"]["image"] == "pgvector/pgvector:pg16"
    assert services["redis"]["image"] == "redis:7-alpine"
    assert services["temporal"]["image"] == "temporalio/auto-setup:1.24"
    assert services["temporal-ui"]["image"] == "temporalio/ui:2.31"
    assert services["otel-collector"]["image"] == "otel/opentelemetry-collector-contrib:0.104.0"
    assert services["jaeger"]["image"] == "jaegertracing/all-in-one:1.59"


def test_initial_schema_uses_manifest_risk_tier_names() -> None:
    schema = (ROOT / "infra" / "migrations" / "001_initial_schema.sql").read_text(encoding="utf-8")

    assert "risk_level" not in schema
    assert "tool_risk_class" not in schema

    required_columns = {
        "agents": "risk_tier TEXT NOT NULL CHECK",
        "skills": "risk_tier TEXT NOT NULL CHECK",
        "run_steps": "risk_tier TEXT CHECK",
        "tool_endpoints": "risk_tier TEXT NOT NULL CHECK",
    }
    for table_name, column_fragment in required_columns.items():
        create_table_start = schema.index(f"CREATE TABLE {table_name}")
        create_table_end = schema.index(");", create_table_start)
        assert column_fragment in schema[create_table_start:create_table_end]
