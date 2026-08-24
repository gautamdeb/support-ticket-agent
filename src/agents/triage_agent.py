from __future__ import annotations

from ..utils.constants import Category
from ..utils.helpers import routing_rules
from ..utils.llm_client import LLMClient, get_llm_client
from ..utils.schemas import RouteDecision, Ticket
from .routing_rules import RuleBook

_CATEGORY_KEYWORDS = {
    Category.REFUND_REQUEST.value: ["refund", "money back", "reimburse", "charged", "charge back"],
    Category.SUBSCRIPTION_CANCELLATION.value: ["cancel", "unsubscribe", "auto-renew", "don't renew", "downgrade"],
    Category.LOGIN_ACCOUNT_ACCESS.value: ["password", "log in", "login", "sign in", "locked", "2fa", "two-factor", "reset", "access my account", "can't access"],
    Category.PRODUCT_TROUBLESHOOTING.value: ["error", "blank", "not working", "doesn't work", "broken", "bug", "crash", "sync", "export", "loading"],
    Category.ABUSIVE_MESSAGE.value: [],
}

_CATEGORY_SYSTEM = (
    "Classify the support ticket into exactly one category: refund_request, "
    "subscription_cancellation, login_account_access, product_troubleshooting, "
    "abusive_message, or other. Use 'other' when the request does not clearly "
    "fit one of the named categories (for example questions about discounts, "
    "pricing, features, or anything not listed) - do NOT force an approximate "
    "match. Return strict JSON: {\"category\": \"...\"}."
)

def categorize(ticket: Ticket, is_abusive: bool = False,
               client: LLMClient | None = None) -> str:
    if is_abusive:
        return Category.ABUSIVE_MESSAGE.value
    client = client or get_llm_client()
    text = f"{ticket.subject}\n{ticket.message}".lower()

    if client.available:
        try:
            data = client.chat_json(_CATEGORY_SYSTEM, f"{ticket.subject}\n{ticket.message}", temperature=0.0)
            cat = str(data.get("category", "")).lower()
            if cat in {c.value for c in Category}:
                return cat
            if cat in {"other", "unknown", "unclassified", "none"}:
                return Category.UNKNOWN.value
        except Exception:
            pass

    best, best_score = Category.UNKNOWN.value, 0
    for cat, kws in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in text)
        if score > best_score:
            best, best_score = cat, score
    return best

def compute_confidence(signals: dict) -> float:
    """Signal-based confidence (robust across embedding backends)."""
    if signals.get("abuse_detected") or signals.get("refund_abuse_detected"):
        return 0.9
    if signals.get("requires_escalation"):
        return 0.4
    if signals.get("missing_required_info"):
        return 0.55
    grounded = signals.get("groundedness_score", 0.0) >= 0.4
    if signals.get("policy_supported") and grounded:
        return 0.85
    if signals.get("policy_supported"):
        return 0.65
    return 0.4

_RULE_BOOK = RuleBook()

def decide_route(signals: dict, rule_book: RuleBook | None = None) -> RouteDecision:
    rules = routing_rules()
    signals = dict(signals)
    signals.setdefault("auto_min", rules.get("auto_resolve", {}).get("min_confidence", 0.75))
    signals["confidence_score"] = compute_confidence(signals)
    return (rule_book or _RULE_BOOK).decide(signals)
