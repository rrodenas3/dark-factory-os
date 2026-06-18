from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from dark_factory_governance.risk_registry import RiskRegistry
from pydantic import BaseModel, Field

SkillRiskTier = Literal["low", "medium", "high", "critical"]


class SkillManifest(BaseModel):
    name: str
    description: str
    version: str
    owner: str
    risk_tier: SkillRiskTier
    required_tools: list[str]
    optional_tools: list[str] = Field(default_factory=list)
    memory_reads: list[str] = Field(default_factory=list)
    memory_writes: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    eval_suite: list[str] = Field(default_factory=list)
    effort: str | None = None
    heartbeat: dict[str, str] | None = None


class SkillDefinition(BaseModel):
    path: str
    vertical: str
    manifest: SkillManifest
    body: str


def parse_skill_file(path: Path) -> SkillDefinition:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} is missing YAML frontmatter")

    _, frontmatter, body = text.split("---", 2)
    manifest = SkillManifest.model_validate(yaml.safe_load(frontmatter))
    skill_dir = path.parent.name
    vertical = path.parent.parent.name

    if manifest.name != skill_dir:
        raise ValueError(f"Skill name '{manifest.name}' must match parent directory '{skill_dir}'")

    return SkillDefinition(path=str(path), vertical=vertical, manifest=manifest, body=body.strip())


def discover_skills(skills_root: Path, risk_registry: RiskRegistry) -> list[SkillDefinition]:
    skills = [parse_skill_file(path) for path in sorted(skills_root.glob("*/*/SKILL.md"))]
    for skill in skills:
        validate_skill_tools(skill, risk_registry)
    return skills


def validate_skill_tools(skill: SkillDefinition, risk_registry: RiskRegistry) -> None:
    for tool_name in [*skill.manifest.required_tools, *skill.manifest.optional_tools]:
        risk_registry.require_tool(tool_name)
