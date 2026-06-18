from __future__ import annotations

from pathlib import Path

import yaml


def validate_schema_file(path: Path) -> None:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must parse to an object")
    if raw.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError(f"{path} must declare JSON Schema draft 2020-12")
    if raw.get("type") != "object":
        raise ValueError(f"{path} must describe an object schema")
    if "properties" not in raw:
        raise ValueError(f"{path} must define properties")


def validate_all_schemas(root: Path) -> list[Path]:
    schema_dir = root / "packages" / "py" / "artifacts" / "schemas"
    paths = sorted(schema_dir.glob("*.yaml"))
    if not paths:
        raise ValueError("No artifact schemas found")
    for path in paths:
        validate_schema_file(path)
    return paths


def main() -> None:
    paths = validate_all_schemas(Path.cwd())
    for path in paths:
        print(f"valid schema: {path}")
