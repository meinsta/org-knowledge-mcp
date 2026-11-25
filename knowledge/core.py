"""core.py: the two things the server does, as plain functions. No model runs here: the client
writes the answer, this decides what it may read and whether its claims are sourced.

Reads the hybrid collection a grounding-layer refresh keeps current. Rows carry {text, source, ref}.
"""
import os
import uuid

from fieldkit import gate, qdrant as Q

COLL = os.environ.get("KNOWLEDGE_COLLECTION", "grounding")
K, PER_SOURCE = 6, 3
RULES = ("Answer only from the evidence below. Cite the [id] of the line behind every claim. "
         "If the evidence does not answer the question, say so. Before you reply, pass your claims to `check`.")
NOTHING = "Nothing in the knowledge base matches this question. Say so; do not answer from memory."


def evidence(question, source=""):
    """One lane when `source` is given. Otherwise the top hits of every lane, so docs cannot crowd
    out what customers said and the reverse."""
    if source:
        pts = Q.hybrid_query(COLL, question, limit=K, flt={"must": [{"key": "source", "match": {"value": source}}]})
    else:
        pts = [h for g in Q.hybrid_groups(COLL, question, "source", group_size=PER_SOURCE, depth=50) for h in g["hits"]]
    return [{"id": str(p["id"]), **p["payload"]} for p in pts]


def ask(question, source=""):
    ev = evidence(question, source)
    if not ev:
        return NOTHING
    return RULES + "\n\n" + "\n".join(f"[{e['id']}] ({e['source']} · {e['ref']}) {e['text']}" for e in ev)


def _is_id(s):
    try:
        return bool(uuid.UUID(str(s)))
    except ValueError:
        return False


def check(claims):
    """claims: [{"text", "source_id", "quote"}]. A claim ships when its source_id is a real row and
    that row holds the quote verbatim."""
    found = Q.get(COLL, sorted({c["source_id"] for c in claims if _is_id(c.get("source_id"))}))
    ev = {str(p["id"]): p["payload"]["text"] for p in found}
    ok, bad = gate.crossref_gate(claims, ev, hard=False)
    ok, bad_quote = gate.quote_gate(ok, ev)
    return {"accepted": [c["text"] for c in ok],
            "rejected": [{"text": c.get("text"), "why": why} for c, why in bad + bad_quote]}
