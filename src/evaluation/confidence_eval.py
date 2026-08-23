"""Confidence calibration evaluation."""
from __future__ import annotations

from typing import Any

from ..utils.helpers import app_config

def evaluate_confidence(results: list[dict[str, Any]],
                        expected: dict[str, str]) -> dict[str, Any]:
    auto_min = app_config()["routing"]["auto_resolve_min_confidence"]

    buckets = {"high(>=0.75)": [], "mid(0.45-0.75)": [], "low(<0.45)": []}
    auto_resolve_below_threshold = []

    for r in results:
        tid = r.get("ticket_id")
        conf = float(r.get("confidence_score", 0.0))
        correct = expected.get(tid) == r.get("route_decision") if tid in expected else None

        if conf >= 0.75:
            buckets["high(>=0.75)"].append(correct)
        elif conf >= 0.45:
            buckets["mid(0.45-0.75)"].append(correct)
        else:
            buckets["low(<0.45)"].append(correct)

        if r.get("route_decision") == "AUTO_RESOLVE" and conf < auto_min:
            auto_resolve_below_threshold.append(tid)

    def acc(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    return {
        "auto_resolve_min_confidence": auto_min,
        "bucket_accuracy": {k: {"n": len(v), "accuracy": acc(v)} for k, v in buckets.items()},
        "auto_resolve_below_threshold": auto_resolve_below_threshold,
        "passed": len(auto_resolve_below_threshold) == 0,
    }
