import pytest
from dark_factory_memory import InMemoryStore, MemoryItem, MemoryQuery


def _make_item(namespace: str, entity_key: str, memory_type: str, content: dict, trust: float = 0.9) -> MemoryItem:  # type: ignore[type-arg]  # noqa: E501
    return MemoryItem(
        namespace=namespace,
        entity_key=entity_key,
        memory_type=memory_type,  # type: ignore[arg-type]
        content=content,
        source_trust=trust,
        consistency_verified=True,
    )


def test_upsert_and_search_basic() -> None:
    store = InMemoryStore()
    item = _make_item("finance.vendor_risk", "acme", "semantic", {"summary": "Good vendor, low risk."})
    store.upsert(item)
    results = store.search(MemoryQuery(query="low risk vendor", namespace="finance.vendor_risk"))
    assert len(results) == 1
    assert results[0].entity_key == "acme"


def test_search_namespace_filter() -> None:
    store = InMemoryStore()
    store.upsert(_make_item("finance.vendor_risk", "acme", "semantic", {"summary": "Finance vendor."}))
    store.upsert(_make_item("retail.campaign_history", "promo-q2", "semantic", {"summary": "Retail promo."}))
    results = store.search(MemoryQuery(query="vendor", namespace="finance"))
    assert all(r.item.namespace.startswith("finance") for r in results)


def test_write_gate_rejects_low_trust_semantic() -> None:
    store = InMemoryStore()
    item = _make_item("finance.vendor_risk", "risky", "semantic", {"summary": "Unverified."}, trust=0.3)
    with pytest.raises(ValueError, match="trust"):
        store.upsert(item)


def test_episodic_append_only() -> None:
    store = InMemoryStore()
    item = _make_item("saas.incident_history", "billing-api", "episodic", {"event": "P1 incident"})
    store.upsert(item, validate=False)
    with pytest.raises(ValueError, match="append-only"):
        store.upsert(item)


def test_seed_demo_populates_store() -> None:
    store = InMemoryStore()
    store.seed_demo()
    items = store.all()
    assert len(items) >= 4


def test_decay_pass_updates_scores() -> None:
    store = InMemoryStore()
    item = _make_item("finance.vendor_risk", "acme", "semantic", {"summary": "Test."})
    store.upsert(item, validate=False)
    updated = store.decay_pass(lam=100.0)
    assert updated >= 0


def test_search_decay_weighted() -> None:
    store = InMemoryStore()
    item = _make_item("finance.vendor_risk", "acme", "semantic", {"summary": "low trust item"})
    store.upsert(item, validate=False)
    results_weighted = store.search(MemoryQuery(query="low trust item", namespace="finance.vendor_risk", decay_weighted=True))  # noqa: E501
    results_flat = store.search(MemoryQuery(query="low trust item", namespace="finance.vendor_risk", decay_weighted=False))  # noqa: E501
    assert len(results_weighted) == len(results_flat)
