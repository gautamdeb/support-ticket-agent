"""Pydantic data models for tickets, retrieval, decisions and HITL records."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .constants import Category, ReviewerAction, Route, Sentiment

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ConversationTurn(BaseModel):
    role: str = "customer"
    message: str
    timestamp: str = Field(default_factory=_now_iso)

class Ticket(BaseModel):
    """Incoming support ticket."""

    ticket_id: str
    customer_id: str
    subject: str = ""
    message: str
    conversation_history: list[ConversationTurn] = Field(default_factory=list)
    priority: str = "medium"

class RetrievedChunk(BaseModel):
    """A single retrieved KB chunk with provenance."""

    text: str
    source: str
    score: float = 0.0
    chunk_index: int = 0

class SentimentResult(BaseModel):
    sentiment: Sentiment = Sentiment.NEUTRAL
    is_abusive: bool = False
    is_refund_abuse: bool = False
    rationale: str = ""

class PolicyCheckResult(BaseModel):
    policy_supported: bool = False
    matched_policies: list[str] = Field(default_factory=list)
    missing_required_info: bool = False
    missing_info_prompts: list[str] = Field(default_factory=list)
    rationale: str = ""

class RagAnswer(BaseModel):
    draft: str = ""
    retrieved_sources: list[str] = Field(default_factory=list)
    groundedness_score: float = 0.0
    confidence_score: float = 0.0
    citations: list[str] = Field(default_factory=list)

class RouteDecision(BaseModel):
    route: Route
    confidence_score: float = 0.0
    reason: str = ""
    applied_override: Optional[str] = None

class DraftReply(BaseModel):
    """The final draft handed to the HITL queue."""

    ticket_id: str
    customer_id: str = ""
    category: str = Category.UNKNOWN.value
    draft_reply: str = ""
    route_decision: str = Route.ESCALATE.value
    confidence_score: float = 0.0
    groundedness_score: float = 0.0
    retrieved_sources: list[str] = Field(default_factory=list)
    sentiment: str = Sentiment.NEUTRAL.value
    recheck_loops: int = 0
    retrieval_refinements: int = 0
    created_at: str = Field(default_factory=_now_iso)
    reviewer_action: Optional[str] = None
    reviewer_comments: Optional[str] = None
    final_reply: Optional[str] = None
    status: str = "PENDING_REVIEW"

    def to_hitl_record(self) -> dict[str, Any]:
        """Return the compact HITL record shape."""
        return {
            "ticket_id": self.ticket_id,
            "draft_reply": self.final_reply or self.draft_reply,
            "route_decision": self.route_decision,
            "confidence_score": round(self.confidence_score, 2),
            "retrieved_sources": self.retrieved_sources,
            "reviewer_action": self.reviewer_action,
            "reviewer_comments": self.reviewer_comments,
        }
