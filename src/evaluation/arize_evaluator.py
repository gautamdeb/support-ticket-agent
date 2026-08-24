from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..utils.helpers import (
    app_config, env, load_dotenv_if_present, project_path, read_json, write_json,
)
from .confidence_eval import evaluate_confidence
from .groundedness_eval import evaluate_groundedness
from .route_accuracy_eval import evaluate_routes, load_expected

def log_to_arize(results: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = env("ARIZE_API_KEY")
    space_id = env("ARIZE_SPACE_ID")
    if not api_key or not space_id:
        return {"logged": False, "reason": "ARIZE_API_KEY / ARIZE_SPACE_ID not set."}
    try:
        import pandas as pd
        from arize.pandas.logger import Client
        from arize.utils.types import Environments, ModelTypes, Schema

        df = pd.DataFrame([
            {
                "prediction_id": r["ticket_id"],
                "route_decision": r.get("route_decision"),
                "confidence_score": r.get("confidence_score"),
                "groundedness_score": r.get("groundedness_score"),
                "category": r.get("category"),
            }
            for r in results
        ])
        client = Client(space_id=space_id, api_key=api_key)
        schema = Schema(
            prediction_id_column_name="prediction_id",
            prediction_label_column_name="route_decision",
            prediction_score_column_name="confidence_score",
            tag_column_names=["category", "groundedness_score"],
        )
        response = client.log(
            dataframe=df,
            model_id=env("ARIZE_PROJECT_NAME", "support-ticket-agent"),
            model_version="1.0.0",
            model_type=ModelTypes.SCORE_CATEGORICAL,
            environment=Environments.PRODUCTION,
            schema=schema,
        )
        status = getattr(response, "status_code", None)
        return {"logged": status in (200, None), "rows": len(df), "status_code": status}
    except Exception as exc:
        return {"logged": False, "reason": f"Arize logging skipped ({exc})."}

def _load_results() -> list[dict[str, Any]]:
    path = project_path(app_config()["paths"]["drafted_replies"], "drafted_replies.json")
    if path.exists():
        return read_json(path)
    return []

def run_full_evaluation(results: list[dict[str, Any]] | None = None,
                        run_pipeline_if_empty: bool = True) -> dict[str, Any]:
    load_dotenv_if_present()
    if results is None:
        results = _load_results()
    if not results and run_pipeline_if_empty:
        from ..main import run_pipeline
        from ..utils.schemas import Ticket
        tickets = [Ticket(**t) for t in read_json(project_path(app_config()["paths"]["tickets"]))]
        results = run_pipeline(tickets, review_mode="auto", verbose=False)

    expected = load_expected()
    route_eval = evaluate_routes(results, expected)
    conf_eval = evaluate_confidence(results, expected)
    ground_eval = evaluate_groundedness(results)
    arize_status = log_to_arize(results)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_tickets": len(results),
        "route_accuracy": route_eval,
        "confidence": conf_eval,
        "groundedness": ground_eval,
        "arize": arize_status,
        "overall_passed": bool(route_eval.get("passed") and conf_eval.get("passed")),
    }

    out_dir = app_config()["paths"]["evaluation_reports"]
    write_json(project_path(out_dir, "evaluation_report.json"), report)
    _write_markdown(report, project_path(out_dir, "evaluation_report.md"))
    return report

def _write_markdown(report: dict[str, Any], path) -> None:
    ra = report["route_accuracy"]
    ce = report["confidence"]
    lines = [
        "# Evaluation Report",
        "",
        f"_Generated: {report['generated_at']}_",
        "",
        f"- Tickets evaluated: **{report['n_tickets']}**",
        f"- Route accuracy: **{ra['accuracy']}** (target {ra['target']}) - "
        f"{'PASS' if ra['passed'] else 'FAIL'}",
        f"- AUTO_RESOLVE below-threshold violations: "
        f"**{len(ce['auto_resolve_below_threshold'])}** - "
        f"{'PASS' if ce['passed'] else 'FAIL'}",
        f"- Arize logging: {report['arize'].get('logged')} "
        f"({report['arize'].get('reason', 'ok')})",
        "",
        "## Per-class (precision / recall)",
        "",
        "| Route | TP | FP | FN | Precision | Recall |",
        "|---|---|---|---|---|---|",
    ]
    for label, m in ra["per_class"].items():
        lines.append(
            f"| {label} | {m['tp']} | {m['fp']} | {m['fn']} | "
            f"{m['precision']} | {m['recall']} |"
        )
    if ra["mismatches"]:
        lines += ["", "## Mismatches", ""]
        for mm in ra["mismatches"]:
            lines.append(f"- {mm['ticket_id']}: expected {mm['expected']}, got {mm['got']}")
    else:
        lines += ["", "_No route mismatches._"]
    path.write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    rep = run_full_evaluation()
    ra = rep["route_accuracy"]
    print(f"Route accuracy: {ra['accuracy']} (target {ra['target']}) "
          f"-> {'PASS' if ra['passed'] else 'FAIL'}")
    print(f"Confidence gate: {'PASS' if rep['confidence']['passed'] else 'FAIL'}")
    print(f"Arize: {rep['arize']}")
    print(f"Report written to outputs/evaluation_reports/")
