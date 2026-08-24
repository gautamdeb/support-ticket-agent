from src.hitl.approval_queue import ApprovalQueue
from src.hitl.reviewer_actions import apply_reviewer_action, auto_review
from src.utils.constants import ReviewerAction
from src.utils.schemas import DraftReply

def _draft(tid="TCK-TEST", route="AUTO_RESOLVE", conf=0.9):
    return DraftReply(
        ticket_id=tid, customer_id="CUST-T", category="refund_request",
        draft_reply="Draft body.", route_decision=route, confidence_score=conf,
    )

def test_enqueue_and_list_pending(tmp_path, monkeypatch):
    q = ApprovalQueue()
    q.path = tmp_path / "queue.json"
    q._items = []
    q.enqueue(_draft())
    pending = q.list_pending()
    assert len(pending) == 1
    assert pending[0]["status"] == "PENDING_REVIEW"

def test_approve_sets_final_reply(tmp_path):
    q = ApprovalQueue()
    q.path = tmp_path / "queue.json"
    q._items = []
    q.enqueue(_draft())
    rec = apply_reviewer_action(q, "TCK-TEST", ReviewerAction.APPROVE, "ok")
    assert rec["status"] == "APPROVED"
    assert rec["final_reply"] == "Draft body."
    assert rec["auto_sent"] is False

def test_edit_overrides_reply(tmp_path):
    q = ApprovalQueue()
    q.path = tmp_path / "queue.json"
    q._items = []
    q.enqueue(_draft())
    rec = apply_reviewer_action(q, "TCK-TEST", ReviewerAction.EDIT, "tweaked",
                                edited_text="Edited body.")
    assert rec["final_reply"] == "Edited body."
    assert rec["status"] == "APPROVED"

def test_auto_review_policy():
    action, _ = auto_review(_draft(route="AUTO_RESOLVE", conf=0.9).model_dump())
    assert action == ReviewerAction.APPROVE
    action, _ = auto_review(_draft(route="ESCALATE", conf=0.4).model_dump())
    assert action == ReviewerAction.ESCALATE
    action, _ = auto_review(_draft(route="AUTO_RESOLVE", conf=0.5).model_dump())
    assert action == ReviewerAction.ESCALATE
