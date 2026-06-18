# Evals Package Spec

Implements CLEAR metrics and golden workflow replay.

Golden datasets live in `evals/datasets/{vertical}_goldens.jsonl`.

Trajectory scoring compares expected tool order and required policy outcomes. Boundary judges run after verification and before approval.
