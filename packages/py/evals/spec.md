# Evals Package Spec

The evals package implements the CLEAR framework for measuring agentic workflow quality. It evaluates cost, latency,
efficiency, accuracy, reliability, tool trajectories, policy compliance, and approval behavior.

## CLEAR Dimensions

- Cost: USD per run, broken down by model tokens, retrieval, tool compute, storage, observability, and human review.
- Latency: p50 and p95 runtime in seconds, plus per-node latency.
- Efficiency: tokens per successful step and tool calls per successful outcome.
- Accuracy: task success rate, verifier pass rate, grounding score, and policy citation quality.
- Reliability: tool success rate, retry recovery rate, timeout rate, and approval precision.

## Golden Datasets

Datasets live at:

```text
evals/datasets/{vertical}_goldens.jsonl
```

Each JSONL record contains:

- `input`
- `expected_tools`
- `expected_outcome`
- `policy_constraints`

Vertical datasets:

- `finance_goldens.jsonl`
- `retail_goldens.jsonl`
- `saas_goldens.jsonl`

## Trajectory Eval

For each golden task:

1. Run the workflow with deterministic mocks.
2. Record the actual tool sequence and key arguments.
3. Compare against the expected tool sequence.
4. Score alignment with `tool_args_match_mode`.

Trajectory score includes:

- ordered tool name match
- required tool presence
- forbidden tool absence
- argument match for critical fields
- correct approval gate placement

## LLM-As-Judge

Boundary judging happens after the `verifier` node and before `approval_gate`.

- Score range: `0.0` to `1.0`.
- Passing threshold: `>= 0.8`.
- The judge must use a different model family from the agent. If the agent is Claude, the judge can be GPT-4o.
- Judge prompts must include tool trace, citations, expected outcome, and policy constraints.
- Judge output must be structured JSON.

## Eval Runner

The suite runner:

1. Loads a golden dataset.
2. Runs the target workflow.
3. Captures run trace, costs, tool calls, model usage, approvals, and final outcome.
4. Scores CLEAR metrics and trajectory alignment.
5. Writes an `eval_runs` row with `summary_json`.
6. Emits OTEL spans for suite, case, and scoring phases.

## Sensors

Computational sensors run inline:

- schema validation on every tool call
- cost budget check after each step
- risk tier check before tool execution
- expected state transition check after each node

Inferential sensors run at boundaries:

- LLM judge after `verifier`
- approval-readiness judge before `approval_gate`
- memory-write contradiction check before durable upsert

## Pass Criteria

A suite passes when:

- all required schemas validate
- no forbidden tools are called
- CLEAR accuracy is at least the suite threshold
- LLM judge score is `>= 0.8`
- destructive and financial actions are gated correctly
- cost and latency stay within configured budget
