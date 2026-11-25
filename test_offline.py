"""Offline checks against an in-memory stand-in for the cluster. Run: python3 test_offline.py"""
from fieldkit import qdrant as Q

from knowledge import core

A, B = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
ROWS = [{"id": A, "payload": {"text": "The old key keeps working for 24 hours.", "source": "docs", "ref": "docs/api-keys"}},
        {"id": B, "payload": {"text": "Security will block the rollout without key rotation.", "source": "field", "ref": "call-001"}}]


def _fake():
    Q.hybrid_query = lambda name, q, limit=6, flt=None, **k: [r for r in ROWS if r["payload"]["source"] == flt["must"][0]["match"]["value"]]
    Q.hybrid_groups = lambda name, q, group_by, **k: [{"id": r["payload"]["source"], "hits": [r]} for r in ROWS]
    Q.get = lambda name, ids: [r for r in ROWS if r["id"] in ids]


def test_ask_cites_ids_and_respects_the_lane():
    _fake()
    out = core.ask("can we rotate keys?")
    assert f"[{A}] (docs · docs/api-keys)" in out and f"[{B}] (field · call-001)" in out and out.startswith(core.RULES)
    assert B not in core.ask("can we rotate keys?", source="docs")
    Q.hybrid_groups = lambda *a, **k: []
    assert core.ask("anything") == core.NOTHING


def test_check_accepts_only_sourced_claims():
    _fake()
    out = core.check([
        {"text": "ok", "source_id": A, "quote": "old key keeps working for 24 hours"},
        {"text": "right id, invented quote", "source_id": A, "quote": "the old key stops working immediately"},
        {"text": "quote from another source", "source_id": B, "quote": "old key keeps working for 24 hours"},
        {"text": "unknown id", "source_id": "33333333-3333-4333-8333-333333333333", "quote": "old key keeps working for 24 hours"},
        {"text": "not an id", "source_id": "docs/api-keys", "quote": "old key keeps working for 24 hours"},
        {"text": "no quote", "source_id": A}])
    assert out["accepted"] == ["ok"] and len(out["rejected"]) == 5


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
