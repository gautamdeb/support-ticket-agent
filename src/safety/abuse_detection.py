from __future__ import annotations

import re

_ABUSIVE_TERMS = [
    "idiot", "idiots", "stupid", "moron", "morons", "garbage", "trash",
    "shut up", "hate you", "hope you", "get fired", "incompetent", "useless",
    "screw you", "damn you", "pathetic",
]
_PROFANITY = ["fuck", "shit", "asshole", "bastard", "bitch", "crap"]
_THREATS = ["or else", "i'll sue", "sue you", "destroy you", "regret this", "come after"]

_REFUND_ABUSE_SIGNALS = [
    "keep asking", "keep requesting", "every week", "until you give in",
    "until you cave", "asked three times", "asked multiple times",
    "chargeback", "dispute the charge", "still using it", "use it daily",
    "using it daily", "i'll just keep",
]

def _contains_any(text: str, terms: list[str]) -> list[str]:
    t = text.lower()
    return [term for term in terms if term in t]

def detect_abuse(text: str) -> dict:
    hits_abusive = _contains_any(text, _ABUSIVE_TERMS)
    hits_prof = _contains_any(text, _PROFANITY)
    hits_threat = _contains_any(text, _THREATS)
    caps_words = re.findall(r"\b[A-Z]{4,}\b", text)
    is_abusive = bool(hits_abusive or hits_prof or hits_threat)
    return {
        "is_abusive": is_abusive,
        "abusive_terms": hits_abusive + hits_prof,
        "threats": hits_threat,
        "caps_shouting": len(caps_words) >= 2,
    }

def detect_refund_abuse(text: str, prior_refund_count_90d: int = 0) -> dict:
    signals = _contains_any(text, _REFUND_ABUSE_SIGNALS)
    repeated = prior_refund_count_90d >= 2
    is_refund_abuse = bool(signals) or repeated
    return {
        "is_refund_abuse": is_refund_abuse,
        "signals": signals,
        "repeated_within_90d": repeated,
        "prior_refund_count_90d": prior_refund_count_90d,
    }
