# Skills Registry Package Spec

The skills registry package loads, validates, activates, and syncs `SKILL.md` files. Skills are the public, versioned
operating procedures that let the platform adapt to any vertical without hardcoding every workflow.

## Discovery

Discovery path:

```text
skills/{vertical}/{skill_name}/SKILL.md
```

The skill name must match the parent directory. For example:

```text
skills/finance/ap-exception-resolution/SKILL.md
```

has name `ap-exception-resolution`.

## Frontmatter

Required fields:

- `name`
- `description`
- `version`
- `owner`
- `risk_tier`
- `required_tools`

Optional fields:

- `optional_tools`
- `memory_reads`
- `memory_writes`
- `triggers`
- `eval_suite`
- `effort`

## Validation Rules

- `name` must match the parent directory.
- `risk_tier` must map to the registry taxonomy used by governance.
- Every `required_tools` entry must exist in `packages/py/governance/risk_registry.yaml`.
- `optional_tools`, when present, must also exist in the risk registry.
- `memory_reads` and `memory_writes` must be declared before the skill can access memory.
- Version changes create a new `skill_versions` row.
- Invalid skills are skipped, reported, and never activated.

## Progressive Disclosure

- L1: name, description, version, owner, risk tier, trigger list. Always loaded at startup.
- L2: full `SKILL.md` body. Loaded when a skill is activated for a run.
- L3: referenced files and examples. Loaded only on demand by the activated skill.

The supervisor should use L1 for routing and only hydrate L2/L3 when needed to control context cost.

## Registry Sync

On startup:

1. Scan the `skills/` directory.
2. Parse frontmatter and body.
3. Validate required fields and tool references.
4. Upsert into `skills`.
5. Upsert the specific version into `skill_versions`.
6. Record validation status and errors.

Database targets:

- `skills.name`
- `skills.current_version`
- `skills.owner_team`
- `skills.risk_tier`
- `skills.status`
- `skill_versions.version`
- `skill_versions.manifest_json`
- `skill_versions.eval_status`

## Activation

`activate_skill(name)` returns:

- L1 metadata
- L2 body
- allowed tools
- memory read/write declarations
- eval suite reference
- trigger metadata

Activation fails closed when required tools are disabled or governance denies the skill risk tier.

## Heartbeat

The registry supports proactive monitoring skills with heartbeat triggers:

- A cron job loads skills with scheduled triggers.
- It calls `activate_skill(name)`.
- It creates a governed run with a generated BriefingScript.
- It records heartbeat outcomes in `episodic_log`.

Heartbeat examples include spend anomaly detection, incident watch, and campaign underperformance monitoring.
