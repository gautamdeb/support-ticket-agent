from __future__ import annotations

from ..utils.constants import ReviewerAction
from .approval_queue import ApprovalQueue
from .reviewer_actions import apply_reviewer_action

_MENU = """
Reviewer actions:
  [a] Approve      [e] Edit         [r] Reject
  [g] Regenerate   [s] Escalate     [k] Skip     [q] Quit
"""

def _print_draft(record: dict) -> None:
    print("=" * 72)
    print(f"Ticket:      {record['ticket_id']}  (customer {record.get('customer_id','?')})")
    print(f"Category:    {record.get('category')}   Sentiment: {record.get('sentiment')}")
    print(f"Route:       {record.get('route_decision')}   "
          f"confidence={record.get('confidence_score')}  "
          f"grounded={record.get('groundedness_score')}")
    print(f"Sources:     {record.get('retrieved_sources')}")
    print("-" * 72)
    print(record.get("draft_reply", ""))
    print("=" * 72)

def run_console() -> None:
    queue = ApprovalQueue()
    pending = queue.list_pending()
    if not pending:
        print("No drafts pending review. Run the pipeline first (python -m src.main).")
        return

    print(f"{len(pending)} draft(s) pending review.")
    for record in pending:
        _print_draft(record)
        print(_MENU)
        choice = input("Action> ").strip().lower()
        if choice == "q":
            break
        if choice == "k":
            continue
        mapping = {
            "a": ReviewerAction.APPROVE, "e": ReviewerAction.EDIT,
            "r": ReviewerAction.REJECT, "g": ReviewerAction.REQUEST_REGENERATION,
            "s": ReviewerAction.ESCALATE,
        }
        action = mapping.get(choice)
        if action is None:
            print("Unrecognised choice; skipping.")
            continue
        edited = None
        if action == ReviewerAction.EDIT:
            print("Enter the edited reply (single line):")
            edited = input("> ")
        comments = input("Comments (optional)> ").strip()
        apply_reviewer_action(queue, record["ticket_id"], action, comments, edited)
        print(f"-> recorded {action.value} for {record['ticket_id']}\n")

    print("Done. Approved drafts are marked ready to send - the system never "
          "sends them automatically.")

if __name__ == "__main__":
    run_console()
