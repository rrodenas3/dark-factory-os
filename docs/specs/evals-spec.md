# Evaluation Spec

## CLEAR Metrics

- Cost: USD per run, per step, and per successful outcome.
- Latency: p50 and p95 run and step latency.
- Efficiency: tokens and tool calls per successful step.
- Accuracy: task success, grounding, policy compliance.
- Reliability: tool success, recovery, duplicate-action prevention.

## Golden Datasets

Datasets live in `evals/datasets/{vertical}_goldens.jsonl`.

Each case includes input, expected skill, expected tool sequence, expected outcome, and policy constraints.

## Sensors

- Inline computational sensors: schema validation, risk policy, budget check, tool allowlist.
- Boundary inferential sensors: LLM judge after verification and before approval.

## Pass Criteria

Local demo evals pass when each vertical smoke case produces the expected skill, required policy citations, and correct approval requirement.
