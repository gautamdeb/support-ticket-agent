"""Conversation memory for a single ticket run."""
from __future__ import annotations

from ..utils.helpers import app_config
from ..utils.schemas import Ticket
from .customer_thread_store import CustomerThreadStore

class ConversationMemory:
    def __init__(self, store: CustomerThreadStore | None = None) -> None:
        self.store = store or CustomerThreadStore()
        self.max_turns = app_config()["memory"]["max_turns_remembered"]

    def context_for(self, ticket: Ticket) -> dict:
        prior = self.store.get_thread(ticket.customer_id)
        turns = ticket.conversation_history[-self.max_turns:]
        return {
            "customer_id": ticket.customer_id,
            "prior_interactions": prior,
            "prior_count": len(prior),
            "this_thread_turns": [t.model_dump() for t in turns],
        }

    def rendered(self, ticket: Ticket) -> str:
        """Human/LLM-readable memory summary for prompts."""
        ctx = self.context_for(ticket)
        lines = []
        if ctx["prior_interactions"]:
            lines.append("Prior interactions with this customer:")
            for e in ctx["prior_interactions"][-self.max_turns:]:
                lines.append(f"  - [{e.get('timestamp','')}] {e.get('category','')}: {e.get('summary','')}")
        for t in ctx["this_thread_turns"]:
            lines.append(f"  ({t.get('role','customer')}) {t.get('message','')}")
        return "\n".join(lines) if lines else "(no prior history)"

    def refund_requests_last_90d(self, ticket: Ticket) -> int:
        return self.store.count_recent_by_category(
            ticket.customer_id, "refund_request", within_days=90
        )
