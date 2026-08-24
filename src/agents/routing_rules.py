from __future__ import annotations

from typing import Optional

from ..utils.constants import Category, Route
from ..utils.schemas import RouteDecision

GROUNDING_FLOOR = 0.4

class HostileConductRule:
    name = "abusive_content"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if s.get("abuse_detected"):
            return RouteDecision(route=Route.REFUSE, confidence_score=s["confidence_score"],
                                 reason="Abusive content - scripted refusal.",
                                 applied_override=self.name)
        return None

class RefundGamingRule:
    name = "refund_abuse"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if s.get("refund_abuse_detected"):
            return RouteDecision(route=Route.REFUSE, confidence_score=s["confidence_score"],
                                 reason="Suspected refund abuse - scripted refusal.",
                                 applied_override=self.name)
        return None

class SpecialistRequiredRule:
    name = "requires_human_specialist"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if s.get("requires_escalation"):
            return RouteDecision(route=Route.ESCALATE, confidence_score=s["confidence_score"],
                                 reason=s.get("escalation_reason")
                                 or "Documented policy requires a human specialist.",
                                 applied_override=self.name)
        return None

class MissingDetailRule:
    name = "insufficient_ticket_info"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if s.get("missing_required_info"):
            return RouteDecision(route=Route.ASK_MORE_INFO, confidence_score=s["confidence_score"],
                                 reason="Ticket lacks the detail needed to act.",
                                 applied_override=self.name)
        return None

class NoGoverningPolicyRule:
    name = "no_policy_found"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if not s.get("policy_supported") and s.get("category") != Category.PRODUCT_TROUBLESHOOTING.value:
            return RouteDecision(route=Route.ESCALATE, confidence_score=s["confidence_score"],
                                 reason="No supporting policy found - escalate rather than fabricate.",
                                 applied_override=self.name)
        return None

class WeakGroundingRule:
    name = "weak_grounding"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if s.get("groundedness_score", 0.0) < GROUNDING_FLOOR:
            return RouteDecision(route=Route.ESCALATE, confidence_score=s["confidence_score"],
                                 reason="Answer insufficiently grounded in the knowledge base.",
                                 applied_override=self.name)
        return None

class ConfidentResolveRule:
    """A confidence-based claim."""

    name = "confident_resolve"

    def evaluate(self, s: dict) -> Optional[RouteDecision]:
        if s["confidence_score"] >= s.get("auto_min", 0.75):
            return RouteDecision(route=Route.AUTO_RESOLVE, confidence_score=s["confidence_score"],
                                 reason="Grounded, policy-backed and confident.")
        return None

class DefaultEscalateRule:
    name = "default_escalate"

    def evaluate(self, s: dict) -> RouteDecision:
        return RouteDecision(route=Route.ESCALATE, confidence_score=s["confidence_score"],
                             reason="Not confident enough to auto-resolve.")

class RuleBook:
    """Ordered routing chain."""

    def __init__(self, rules: Optional[list] = None) -> None:
        self._rules = rules or [
            HostileConductRule(),
            RefundGamingRule(),
            SpecialistRequiredRule(),
            MissingDetailRule(),
            NoGoverningPolicyRule(),
            WeakGroundingRule(),
            ConfidentResolveRule(),
            DefaultEscalateRule(),
        ]

    def decide(self, signals: dict) -> RouteDecision:
        for rule in self._rules:
            verdict = rule.evaluate(signals)
            if verdict is not None:
                return verdict
        return DefaultEscalateRule().evaluate(signals)
