from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..utils.constants import Route
from ..utils.helpers import app_config, project_path, read_json

def load_expected() -> dict[str, str]:
    return read_json(project_path(app_config()["paths"]["expected_routes"]))

def evaluate_routes(results: list[dict[str, Any]],
                    expected: dict[str, str] | None = None) -> dict[str, Any]:
    expected = expected or load_expected()
    labels = Route.values()
    confusion: dict[str, dict[str, int]] = {a: defaultdict(int) for a in labels}

    correct = 0
    total = 0
    mismatches = []
    for r in results:
        tid = r.get("ticket_id")
        if tid not in expected:
            continue
        total += 1
        exp = expected[tid]
        got = r.get("route_decision")
        confusion[exp][got] += 1
        if exp == got:
            correct += 1
        else:
            mismatches.append({"ticket_id": tid, "expected": exp, "got": got})

    per_class = {}
    for label in labels:
        tp = confusion[label][label]
        fn = sum(v for k, v in confusion[label].items() if k != label)
        fp = sum(confusion[o][label] for o in labels if o != label)
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        per_class[label] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 3) if precision is not None else None,
            "recall": round(recall, 3) if recall is not None else None,
        }

    accuracy = round(correct / total, 4) if total else None
    target = app_config()["evaluation"]["route_accuracy_target"]
    return {
        "n": total,
        "accuracy": accuracy,
        "target": target,
        "passed": (accuracy is not None and accuracy >= target),
        "mismatches": mismatches,
        "per_class": per_class,
        "confusion": {k: dict(v) for k, v in confusion.items()},
    }
