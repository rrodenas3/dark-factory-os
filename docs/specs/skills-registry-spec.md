# Skills Registry Spec

## Discovery

Skills live at:

```text
skills/{vertical}/{skill_name}/SKILL.md
```

## Required Frontmatter

- `name`
- `description`
- `version`
- `owner`
- `risk_tier`
- `required_tools`

## Optional Frontmatter

- `optional_tools`
- `memory_reads`
- `memory_writes`
- `triggers`
- `eval_suite`
- `effort`
- `heartbeat`

## Validation

- Skill name matches parent directory.
- Risk tier is `low`, `medium`, `high`, or `critical`.
- Required tools exist in `packages/py/governance/risk_registry.yaml`.
- Memory reads and writes are declared.
- Skill body contains goal, context, procedure, verification, and failure handling.

## Self-Improvement

Agents may generate SkillImprovementProposal artifacts from repeated failures or user corrections. Proposals must pass validation and evals, then open a human-reviewed PR before publication.
