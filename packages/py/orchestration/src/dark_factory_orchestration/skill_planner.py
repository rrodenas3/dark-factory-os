from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dark_factory_governance.risk_registry import RiskRegistry
from dark_factory_skills_registry.loader import SkillDefinition, discover_skills

CONTROL_PLANE_TOOLS = {"approvals.request"}
DEFAULT_CONTEXT_TOOLS = {"policy.search", "memory.search", "kg.query"}
FALLBACK_PLAN = ["policy.search", "memory.search"]


def resolve_skill_plan(
    skill_name: str,
    risk_registry: RiskRegistry,
    *,
    skills_root: Path | None = None,
) -> list[str]:
    """Resolve the executable tool plan declared by a SKILL.md manifest."""
    skill = _skills_by_name(risk_registry, skills_root)[skill_name]
    manifest = skill.manifest
    required_tools = [tool for tool in manifest.required_tools if tool not in CONTROL_PLANE_TOOLS]
    contextual_tools = _read_only_optional_tools(manifest.optional_tools, risk_registry)

    plan: list[str] = []
    inserted_context = False
    for tool_name in required_tools:
        policy = risk_registry.require_tool(tool_name)
        if not inserted_context and policy.risk_tier in ("financial", "destructive"):
            plan.extend(contextual_tools)
            inserted_context = True
        plan.append(tool_name)
        if policy.risk_tier in ("financial", "destructive"):
            break

    if not inserted_context:
        plan.extend(contextual_tools)

    return _dedupe(plan)


def load_fallback_plan(risk_registry: RiskRegistry) -> list[str]:
    """Return the safe read-only fallback after validating it against policy."""
    return [tool_name for tool_name in FALLBACK_PLAN if risk_registry.require_tool(tool_name)]


def _read_only_optional_tools(tool_names: list[str], risk_registry: RiskRegistry) -> list[str]:
    tools: list[str] = []
    for tool_name in tool_names:
        if tool_name in CONTROL_PLANE_TOOLS:
            continue
        policy = risk_registry.require_tool(tool_name)
        if policy.risk_tier == "read_only" and tool_name in DEFAULT_CONTEXT_TOOLS:
            tools.append(tool_name)
    return tools


def _dedupe(tool_names: list[str]) -> list[str]:
    seen: set[str] = set()
    plan: list[str] = []
    for tool_name in tool_names:
        if tool_name in seen:
            continue
        seen.add(tool_name)
        plan.append(tool_name)
    return plan


def _skills_by_name(risk_registry: RiskRegistry, skills_root: Path | None) -> dict[str, SkillDefinition]:
    root = skills_root or _find_repo_root(Path(__file__).resolve()) / "skills"
    if skills_root is None:
        return _cached_skills_by_name(root)

    return {skill.manifest.name: skill for skill in discover_skills(root, risk_registry)}


@lru_cache(maxsize=1)
def _cached_skills_by_name(skills_root: Path) -> dict[str, SkillDefinition]:
    registry = _load_registry_for_skills_root(skills_root)
    return {skill.manifest.name: skill for skill in discover_skills(skills_root, registry)}


def _load_registry_for_skills_root(skills_root: Path) -> RiskRegistry:
    from dark_factory_governance.risk_registry import load_risk_registry

    root = _find_repo_root(skills_root)
    return load_risk_registry(root / "packages" / "py" / "governance" / "risk_registry.yaml")


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "skills").exists() and (
            candidate / "packages" / "py" / "governance" / "risk_registry.yaml"
        ).exists():
            return candidate
    raise FileNotFoundError("Could not find repository root containing skills/ and risk_registry.yaml")
