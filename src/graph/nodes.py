"""Graph node functions."""
from __future__ import annotations

from typing import Any

from ..agents.policy_agent import check_policy
from ..agents.rag_agent import draft_answer
from ..agents.response_agent import compose_response
from ..agents.sentiment_agent import analyze_sentiment
from ..agents.triage_agent import categorize, decide_route
from ..logging.audit_logger import build_audit_record, write_audit_record
from ..safety.escalation_rules import requires_human
from ..utils.helpers import app_config

def _tracer(state: dict):
    return state.get("_tracer")

def sentiment_policy_node(state: dict[str, Any]) -> dict[str, Any]:
    """'Sentiment & Policy Check' + retrieval (support requires retrieval)."""
    ticket = state["ticket"]
    client = state.get("_client")
    retriever = state.get("_retriever")
    memory = state.get("_memory")
    tr = _tracer(state)

    prior_refunds = memory.refund_requests_last_90d(ticket) if memory else 0

    sent = analyze_sentiment(ticket, prior_refunds, client)
    category = categorize(ticket, sent.is_abusive, client)

    query = f"{ticket.subject}\n{ticket.message}".strip()
    refinement = state.get("retrieval_refinements", 0)
    retrieved = retriever.retrieve(query, category=category, refinement=refinement) if retriever else []

    policy = check_policy(category, ticket, retrieved)
    needs_human, escalation_reason = requires_human(category, ticket)

    if tr:
        tr.log("sentiment_policy", "classified",
               {"category": category, "sentiment": sent.sentiment.value,
                "abuse": sent.is_abusive, "refund_abuse": sent.is_refund_abuse,
                "policy_supported": policy.policy_supported,
                "requires_escalation": needs_human,
                "retrieved": [r.source for r in retrieved], "refinement": refinement})

    refusal_template = ""
    if sent.is_abusive:
        refusal_template = "abusive_content"
    elif sent.is_refund_abuse:
        refusal_template = "refund_abuse"

    return {
        "prior_refund_count_90d": prior_refunds,
        "sentiment": sent.sentiment.value,
        "abuse_detected": sent.is_abusive,
        "refund_abuse_detected": sent.is_refund_abuse,
        "refusal_template": refusal_template,
        "category": category,
        "retrieved": retrieved,
        "retrieved_sources": sorted({r.source for r in retrieved}),
        "policy_supported": policy.policy_supported,
        "matched_policies": policy.matched_policies,
        "missing_required_info": policy.missing_required_info,
        "missing_info_prompts": policy.missing_info_prompts,
        "requires_escalation": needs_human,
        "escalation_reason": escalation_reason,
    }

def rag_answer_node(state: dict[str, Any]) -> dict[str, Any]:
    """'RAG Answer Draft'."""
    ticket = state["ticket"]
    client = state.get("_client")
    rag = draft_answer(ticket, state.get("retrieved", []),
                       state.get("policy_supported", False), client)
    tr = _tracer(state)
    if tr:
        tr.log("rag_answer", "drafted",
               {"groundedness": rag.groundedness_score, "confidence": rag.confidence_score,
                "sources": rag.retrieved_sources})
    return {
        "rag_answer": rag,
        "groundedness_score": rag.groundedness_score,
        "confidence_score": rag.confidence_score,
        "retrieved_sources": rag.retrieved_sources or state.get("retrieved_sources", []),
    }

def route_decision_node(state: dict[str, Any]) -> dict[str, Any]:
    """'LangGraph Route Decision' - base proposal + safety overrides."""
    signals = {
        "confidence_score": state.get("confidence_score", 0.0),
        "groundedness_score": state.get("groundedness_score", 0.0),
        "policy_supported": state.get("policy_supported", False),
        "missing_required_info": state.get("missing_required_info", False),
        "abuse_detected": state.get("abuse_detected", False),
        "refund_abuse_detected": state.get("refund_abuse_detected", False),
        "requires_escalation": state.get("requires_escalation", False),
        "category": state.get("category", "unknown"),
    }
    decision = decide_route(signals)
    reason = decision.reason
    if decision.route.value == "ESCALATE" and state.get("escalation_reason"):
        reason = state["escalation_reason"]
    tr = _tracer(state)
    if tr:
        tr.log("route_decision", "decided",
               {"route": decision.route.value, "confidence": decision.confidence_score,
                "override": decision.applied_override, "reason": reason})
    return {
        "route": decision.route.value,
        "route_reason": reason,
        "applied_override": decision.applied_override,
        "confidence_score": decision.confidence_score,
    }

def recheck_node(state: dict[str, Any]) -> dict[str, Any]:
    """Confidence re-check loop body: widen retrieval and try again."""
    tr = _tracer(state)
    loops = state.get("recheck_loops", 0) + 1
    refinements = state.get("retrieval_refinements", 0) + 1
    if tr:
        tr.log("confidence_recheck", "refine",
               {"loop": loops, "confidence": state.get("confidence_score", 0.0)})
    return {"recheck_loops": loops, "retrieval_refinements": refinements}

def compose_node(state: dict[str, Any]) -> dict[str, Any]:
    """Compose the final draft reply for the HITL queue."""
    ticket = state["ticket"]
    draft = compose_response(ticket, state)
    tr = _tracer(state)
    if tr:
        tr.log("compose_response", "drafted", {"route": draft.route_decision})
    return {"draft": draft}

def audit_node(state: dict[str, Any]) -> dict[str, Any]:
    """Write the audit record and update customer memory. NEVER auto-sends."""
    tr = _tracer(state)
    if tr:
        state["trace"] = tr.as_list()
    record = build_audit_record(state)
    write_audit_record(record)

    memory = state.get("_memory")
    if memory is not None:
        ticket = state["ticket"]
        memory.store.record_interaction(
            ticket.customer_id, ticket.ticket_id,
            state.get("category", "unknown"),
            summary=f"{state.get('route')} ({state.get('route_reason','')})",
        )
    if tr:
        tr.log("audit_log", "written", {"route": state.get("route")})
    return {"audit_record": record}

def after_route(state: dict[str, Any]) -> str:
    """Decide whether to run the confidence re-check loop or move on."""
    cfg = app_config()["routing"]
    conf = state.get("confidence_score", 0.0)
    loops = state.get("recheck_loops", 0)

    if state.get("applied_override"):
        return "compose"
    if state.get("abuse_detected") or state.get("missing_required_info"):
        return "compose"
    if cfg["recheck_low"] <= conf < cfg["recheck_high"] and loops < cfg["max_recheck_loops"]:
        return "recheck"
    return "compose"
