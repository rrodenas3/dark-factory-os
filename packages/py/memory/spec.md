# Memory Package Spec

Implements working, episodic, semantic, procedural, and graph memory interfaces.

Public functions planned:

- `search(query, namespace, memory_type, k)`
- `upsert(item, validate=True)`
- `decay_pass()`

Read gates filter by access scope, namespace, memory type, consistency, and decay-weighted similarity. Write gates check type, trust, schema, and contradictions.
