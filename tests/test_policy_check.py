from src.agents.policy_agent import check_policy
from src.retrieval.retriever import get_retriever
from src.safety.escalation_rules import requires_human
from src.utils.constants import Category
from src.utils.schemas import Ticket

def _t(msg, subject="", cid="CUST-X", tid="T"):
    return Ticket(ticket_id=tid, customer_id=cid, subject=subject, message=msg)

def test_unknown_category_is_not_policy_supported():
    r = get_retriever()
    ticket = _t("Do you offer a student discount?")
    chunks = r.retrieve(ticket.message, category=Category.UNKNOWN.value)
    res = check_policy(Category.UNKNOWN.value, ticket, chunks)
    assert res.policy_supported is False

def test_refund_category_is_policy_supported():
    r = get_retriever()
    ticket = _t("I was charged yesterday and want a refund.")
    chunks = r.retrieve(ticket.message, category=Category.REFUND_REQUEST.value)
    res = check_policy(Category.REFUND_REQUEST.value, ticket, chunks)
    assert res.policy_supported is True
    assert "refund_policy.md" in res.matched_policies

def test_refund_outside_window_requires_human():
    needs, reason = requires_human(Category.REFUND_REQUEST.value,
                                   _t("Refund my charge from 40 days ago"))
    assert needs is True
    assert "7-day" in reason

def test_refund_within_window_does_not_require_human():
    needs, _ = requires_human(Category.REFUND_REQUEST.value,
                              _t("I was charged yesterday, please refund"))
    assert needs is False

def test_2fa_requires_human():
    needs, _ = requires_human(Category.LOGIN_ACCOUNT_ACCESS.value,
                              _t("I lost my authenticator app for two-factor"))
    assert needs is True

def test_vague_troubleshooting_missing_info():
    res = check_policy(Category.PRODUCT_TROUBLESHOOTING.value,
                       _t("its broken please help", subject="it doesn't work"), [])
    assert res.missing_required_info is True
    assert res.missing_info_prompts
