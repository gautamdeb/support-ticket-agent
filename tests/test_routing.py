"""End-to-end routing accuracy against the golden dataset (mock mode)."""
from src.evaluation.route_accuracy_eval import evaluate_routes

def test_all_routes_match_golden(pipeline_results, expected_routes):
    result = evaluate_routes(pipeline_results, expected_routes)
    assert result["accuracy"] == 1.0, f"Route mismatches: {result['mismatches']}"

def test_four_routes_are_used(pipeline_results):
    routes = {r["route_decision"] for r in pipeline_results}
    assert routes == {"AUTO_RESOLVE", "ESCALATE", "REFUSE", "ASK_MORE_INFO"}

def test_no_auto_send(pipeline_results):
    for r in pipeline_results:
        assert r.get("auto_sent") in (False, None)

def test_auto_resolve_requires_confidence(pipeline_results):
    for r in pipeline_results:
        if r["route_decision"] == "AUTO_RESOLVE":
            assert r["confidence_score"] >= 0.75
