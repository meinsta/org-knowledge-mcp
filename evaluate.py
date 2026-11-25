"""evaluate.py: does `ask` surface each golden answer, and does `check` tell a sourced claim from a
made-up one? Needs the cluster and a collection built by grounding-layer.

    python3 evaluate.py
"""
import json, os

from fieldkit import recall

from knowledge import core

gold = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden.json")))


def main():
    r = recall.hit_rate(gold, lambda q: [e["text"] for e in core.evidence(q)])
    print(f"ask: {r['hits']}/{r['questions']} golden questions get their answer in the evidence; missed: {r['missed']}")
    passed = 0
    for g in gold:
        hit = {e["text"]: e["id"] for e in core.evidence(g["q"])}
        sid = next((hit[t] for t in g["target"] if t in hit), None)
        if not sid:
            continue
        quote = next(t for t in g["target"] if t in hit)
        out = core.check([{"text": "sourced", "source_id": sid, "quote": quote},
                          {"text": "wrong quote", "source_id": sid, "quote": "this sentence appears in no source at all"},
                          {"text": "wrong id", "source_id": "00000000-0000-4000-8000-000000000000", "quote": quote}])
        passed += out["accepted"] == ["sourced"] and len(out["rejected"]) == 2
    print(f"check: {passed}/{r['hits']} accept the sourced claim and reject both made-up ones")
    return r["hits"] == r["questions"] == passed


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
