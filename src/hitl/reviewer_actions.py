"""Apply a reviewer's decision to a queued draft."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..utils.constants import ReviewerAction
from .approval_queue import ApprovalQueue

def apply_reviewer_action(
    queue: ApprovalQueue,
    ticket_id: str,
    action: ReviewerAction | str,
    comments: str = "",
    edited_text: Optional[str] = None,
) -> dict[str, Any]:
    action = ReviewerAction(action) if not isinstance(action, ReviewerAction) else action
    record = queue.get(ticket_id)
    if record is None:
        raise KeyError(f"No queued draft for ticket {ticket_id}")

    record["reviewer_action"] = action.value
    record["reviewer_comments"] = comments
    record["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    if action == ReviewerAction.APPROVE:
        record["status"] = "APPROVED"
        record["final_reply"] = record.get("draft_reply")
    elif action == ReviewerAction.EDIT:
        record["status"] = "APPROVED"
        record["final_reply"] = edited_text or record.get("draft_reply")
    elif action == ReviewerAction.REJECT:
        record["status"] = "REJECTED"
    elif action == ReviewerAction.REQUEST_REGENERATION:
        record["status"] = "REGENERATE"
    elif action == ReviewerAction.ESCALATE:
        record["status"] = "ESCALATED"
        record["route_decision"] = "ESCALATE"

    record["auto_sent"] = False
    queue.update(record)
    return record

def auto_review(record: dict[str, Any]) -> tuple[ReviewerAction, str]:
    """A stand-in reviewer policy for unattended demo runs."""
    route = record.get("route_decision")
    conf = float(record.get("confidence_score", 0.0))
    if route == "AUTO_RESOLVE" and conf >= 0.75:
        return ReviewerAction.APPROVE, "Auto-review: grounded, policy-backed, high confidence."
    if route == "REFUSE":
        return ReviewerAction.APPROVE, "Auto-review: scripted refusal is appropriate."
    if route == "ASK_MORE_INFO":
        return ReviewerAction.APPROVE, "Auto-review: clarification request is appropriate."
    return ReviewerAction.ESCALATE, "Auto-review: routing to a human specialist."
