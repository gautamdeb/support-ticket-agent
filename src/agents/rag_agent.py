from __future__ import annotations

from ..evaluation.groundedness_eval import groundedness_score
from ..utils.llm_client import LLMClient, get_llm_client
from ..utils.schemas import RagAnswer, RetrievedChunk, Ticket

_SYSTEM = (
    "You are a customer-support drafting assistant. Answer the customer using "
    "ONLY the policy/FAQ context provided. Quote policy wording where relevant. "
    "If the context does not contain the answer, say the policy could not be "
    "verified and that the ticket should be escalated - do NOT invent policy. "
    "End with a 'Sources:' line listing the source filenames you used. "
    "Write a concise, friendly draft reply to the customer."
)

def _context_block(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[source: {c.source}]\n{c.text}")
    return "\n\n---\n\n".join(parts)

def _extractive_draft(ticket: Ticket, chunks: list[RetrievedChunk]) -> str:
    """Offline draft: lead line + the most relevant policy excerpt + sources."""
    if not chunks:
        return (
            "Thanks for reaching out. I couldn't verify this against our current "
            "policies, so I'm routing it to a specialist who can help."
        )
    top = chunks[0]
    excerpt = top.text.strip()
    if len(excerpt) > 600:
        excerpt = excerpt[:600].rsplit(" ", 1)[0] + "..."
    sources = ", ".join(sorted({c.source for c in chunks}))
    return (
        f"Hi, thanks for contacting support about \"{ticket.subject or ticket.message[:40]}\".\n\n"
        f"Based on our policy:\n{excerpt}\n\n"
        f"If anything above doesn't match your situation, let us know and we'll help further.\n\n"
        f"Sources: {sources}"
    )

def draft_answer(
    ticket: Ticket,
    chunks: list[RetrievedChunk],
    policy_supported: bool,
    client: LLMClient | None = None,
) -> RagAnswer:
    client = client or get_llm_client()
    sources = sorted({c.source for c in chunks})
    context_texts = [c.text for c in chunks]

    if client.available and chunks:
        try:
            user = (
                f"CONTEXT:\n{_context_block(chunks)}\n\n"
                f"CUSTOMER TICKET:\nSubject: {ticket.subject}\nMessage: {ticket.message}"
            )
            draft = client.chat(_SYSTEM, user, temperature=0.1)
        except Exception:
            draft = _extractive_draft(ticket, chunks)
    else:
        draft = _extractive_draft(ticket, chunks)

    ground = groundedness_score(draft, context_texts)

    top_score = chunks[0].score if chunks else 0.0
    confidence = round(
        0.45 * min(top_score, 1.0)
        + 0.35 * ground
        + 0.20 * (1.0 if policy_supported else 0.0),
        4,
    )

    return RagAnswer(
        draft=draft,
        retrieved_sources=sources,
        groundedness_score=ground,
        confidence_score=confidence,
        citations=sources,
    )
