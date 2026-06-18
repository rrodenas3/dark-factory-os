# Skills Registry Package Spec

Discovery path: `skills/{vertical}/{skill_name}/SKILL.md`.

The registry loads L1 metadata for all skills, L2 body on activation, and L3 references on demand. It validates required tools against `packages/py/governance/risk_registry.yaml` and syncs metadata into the database.
