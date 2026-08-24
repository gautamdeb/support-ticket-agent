from src.safety.abuse_detection import detect_abuse, detect_refund_abuse
from src.safety.refusal_templates import get_refusal

def test_abusive_message_detected():
    res = detect_abuse("You people are complete idiots and I hope you get fired.")
    assert res["is_abusive"] is True

def test_polite_message_not_abusive():
    res = detect_abuse("Hi, could you please help me reset my password?")
    assert res["is_abusive"] is False

def test_refund_abuse_signals():
    res = detect_refund_abuse("I'll just keep requesting until you give in, still using it daily")
    assert res["is_refund_abuse"] is True

def test_repeated_refunds_flagged():
    res = detect_refund_abuse("refund please", prior_refund_count_90d=3)
    assert res["is_refund_abuse"] is True
    assert res["repeated_within_90d"] is True

def test_refusal_templates_exist():
    assert "resubmit" in get_refusal("abusive_content").lower()
    assert get_refusal("refund_abuse")
    assert get_refusal("does_not_exist")

def test_refuse_route_uses_scripted_template(pipeline_results):
    refusals = [r for r in pipeline_results if r["route_decision"] == "REFUSE"]
    assert refusals
    for r in refusals:
        assert len(r["draft_reply"]) > 20
