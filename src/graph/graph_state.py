from __future__ import annotations

from typing import Any, TypedDict

from ..utils.schemas import Ticket

class GraphState(TypedDict, total=False):
    ticket: Ticket
    ticket_id: str
    customer_id: str
    prior_refund_count_90d: int
    memory_summary: str

    category: str
    sentiment: str
    abuse_detected: bool
    refund_abuse_detected: bool
    refusal_template: str
    policy_supported: bool
    matched_policies: list[str]
    missing_required_info: bool
    missing_info_prompts: list[str]
    requires_escalation: bool
    escalation_reason: str

    retrieved: list
    retrieved_sources: list[str]
    rag_answer: Any
    groundedness_score: float
    confidence_score: float

    route: str
    route_reason: str
    applied_override: str | None

    recheck_loops: int
    retrieval_refinements: int

    draft: Any
    trace: list
    audit_record: dict

    _client: Any
    _retriever: Any
    _memory: Any
    _tracer: Any

def init_state(ticket: Ticket, services: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": ticket,
        "ticket_id": ticket.ticket_id,
        "customer_id": ticket.customer_id,
        "prior_refund_count_90d": 0,
        "category": "unknown",
        "sentiment": "neutral",
        "abuse_detected": False,
        "refund_abuse_detected": False,
        "refusal_template": "",
        "policy_supported": False,
        "matched_policies": [],
        "missing_required_info": False,
        "missing_info_prompts": [],
        "requires_escalation": False,
        "escalation_reason": "",
        "retrieved": [],
        "retrieved_sources": [],
        "rag_answer": None,
        "groundedness_score": 0.0,
        "confidence_score": 0.0,
        "route": "ESCALATE",
        "route_reason": "",
        "applied_override": None,
        "recheck_loops": 0,
        "retrieval_refinements": 0,
        "draft": None,
        "trace": [],
        "_client": services.get("client"),
        "_retriever": services.get("retriever"),
        "_memory": services.get("memory"),
        "_tracer": services.get("tracer"),
    }
