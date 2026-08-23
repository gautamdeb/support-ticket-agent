"""Sentiment & abuse agent (first half of 'Sentiment & Policy Check')."""
from __future__ import annotations

from ..safety.abuse_detection import detect_abuse, detect_refund_abuse
from ..utils.constants import Sentiment
from ..utils.llm_client import LLMClient, get_llm_client
from ..utils.schemas import SentimentResult, Ticket

_SYSTEM = (
    "You are a support triage assistant. Classify the customer's message. "
    "Return strict JSON with keys: sentiment (one of positive, neutral, "
    "negative, abusive), is_abusive (bool), rationale (short string). "
    "Judge only the tone; do not resolve the request."
)

def analyze_sentiment(
    ticket: Ticket,
    prior_refund_count_90d: int = 0,
    client: LLMClient | None = None,
) -> SentimentResult:
    client = client or get_llm_client()
    text = f"{ticket.subject}\n{ticket.message}".strip()

    abuse = detect_abuse(text)
    refund_abuse = detect_refund_abuse(text, prior_refund_count_90d)

    sentiment = Sentiment.NEUTRAL
    rationale = ""

    if client.available:
        try:
            data = client.chat_json(_SYSTEM, text, temperature=0.0)
            raw = str(data.get("sentiment", "neutral")).lower()
            sentiment = Sentiment(raw) if raw in {s.value for s in Sentiment} else Sentiment.NEUTRAL
            if data.get("is_abusive"):
                abuse["is_abusive"] = True
            rationale = str(data.get("rationale", ""))
        except Exception:
            pass

    if abuse["is_abusive"]:
        sentiment = Sentiment.ABUSIVE
    elif not client.available:
        sentiment = Sentiment.NEGATIVE if abuse["caps_shouting"] else Sentiment.NEUTRAL

    if not rationale:
        rationale = (
            f"lexical abuse={abuse['is_abusive']} "
            f"refund_abuse={refund_abuse['is_refund_abuse']} "
            f"(prior refunds 90d={prior_refund_count_90d})"
        )

    return SentimentResult(
        sentiment=sentiment,
        is_abusive=abuse["is_abusive"],
        is_refund_abuse=refund_abuse["is_refund_abuse"],
        rationale=rationale,
    )
