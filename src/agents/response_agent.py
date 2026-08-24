from __future__ import annotations

from ..safety.refusal_templates import get_refusal
from ..utils.constants import Route
from ..utils.schemas import DraftReply, Ticket

def _escalation_message(reason: str) -> str:
    return (
        "Thanks for reaching out. Your request needs a closer look from one of "
        "our support specialists, so I've routed it to the right team. They'll "
        "follow up with you directly. We appreciate your patience."
    )

def _ask_more_info_message(prompts: list[str]) -> str:
    bullet = "\n".join(f"  - {p}" for p in prompts) if prompts else "  - A few more details about your issue."
    return (
        "Thanks for getting in touch! To help you quickly, could you share a bit "
        "more detail:\n\n"
        f"{bullet}\n\n"
        "As soon as we have this, we'll get you sorted."
    )

def compose_response(ticket: Ticket, state: dict) -> DraftReply:
    route = Route(state["route"])
    rag = state.get("rag_answer")

    if route == Route.AUTO_RESOLVE and rag is not None:
        draft_text = rag.draft
    elif route == Route.ASK_MORE_INFO:
        draft_text = _ask_more_info_message(state.get("missing_info_prompts", []))
    elif route == Route.REFUSE:
        template_key = state.get("refusal_template") or (
            "refund_abuse" if state.get("refund_abuse_detected") else "abusive_content"
        )
        draft_text = get_refusal(template_key)
    else:
        draft_text = _escalation_message(state.get("route_reason", ""))

    return DraftReply(
        ticket_id=ticket.ticket_id,
        customer_id=ticket.customer_id,
        category=state.get("category", "unknown"),
        draft_reply=draft_text,
        route_decision=route.value,
        confidence_score=float(state.get("confidence_score", 0.0)),
        groundedness_score=float(state.get("groundedness_score", 0.0)),
        retrieved_sources=state.get("retrieved_sources", []),
        sentiment=state.get("sentiment", "neutral"),
        recheck_loops=state.get("recheck_loops", 0),
        retrieval_refinements=state.get("retrieval_refinements", 0),
        status="PENDING_REVIEW",
    )
