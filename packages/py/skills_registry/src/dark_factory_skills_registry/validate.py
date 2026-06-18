from __future__ import annotations

from pathlib import Path

from dark_factory_governance.risk_registry import load_risk_registry

from dark_factory_skills_registry.loader import discover_skills


def main() -> None:
    root = Path.cwd()
    registry = load_risk_registry(root / "packages" / "py" / "governance" / "risk_registry.yaml")
    skills = discover_skills(root / "skills", registry)
    for skill in skills:
        print(f"{skill.vertical}/{skill.manifest.name}: {len(skill.manifest.required_tools)} required tools")
