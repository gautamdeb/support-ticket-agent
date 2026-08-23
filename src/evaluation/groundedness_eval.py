"""Groundedness scoring: how much of the draft is supported by retrieved context."""
from __future__ import annotations

import re

_STOP = set(
    "the a an and or of to for in on at is are was be as your you we our it this "
    "that with can will please if not do does have has i my me they them their".split()
)
_WORD = re.compile(r"[a-z0-9]+")

def _content_words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 2}

def groundedness_score(draft: str, context_texts: list[str]) -> float:
    """Fraction of the draft's content words that appear in the context."""
    draft_words = _content_words(draft)
    if not draft_words:
        return 0.0
    context_words: set[str] = set()
    for t in context_texts:
        context_words |= _content_words(t)
    if not context_words:
        return 0.0
    overlap = draft_words & context_words
    return round(len(overlap) / len(draft_words), 4)

def evaluate_groundedness(records: list[dict]) -> dict:
    """Offline batch groundedness over audit records that expected grounding."""
    scored = []
    for r in records:
        route = r.get("route_decision")
        if route != "AUTO_RESOLVE":
            continue
        draft = r.get("draft_reply") or ""
        scored.append(r.get("groundedness_score", 0.0))
    if not scored:
        return {"n": 0, "mean_groundedness": None}
    return {"n": len(scored), "mean_groundedness": round(sum(scored) / len(scored), 4)}
