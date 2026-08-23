"""Audit logging - the final node in the flow."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..utils.helpers import app_config, append_jsonl, project_path, write_json

def _audit_dir() -> Path:
    return project_path(app_config()["paths"]["audit_logs"])

def audit_log_path() -> Path:
    return _audit_dir() / "audit_log.jsonl"

def write_audit_record(record: dict[str, Any]) -> dict[str, Any]:
    """Append one audit record and return it (with a timestamp added)."""
    record = dict(record)
    record.setdefault("logged_at", datetime.now(timezone.utc).isoformat())
    append_jsonl(audit_log_path(), record)
    return record

def build_audit_record(state: dict[str, Any]) -> dict[str, Any]:
    """Construct the audit record from the final graph state."""
    draft = state.get("draft")
    draft_dict = draft.model_dump() if draft is not None and hasattr(draft, "model_dump") else {}
    return {
        "ticket_id": state.get("ticket_id"),
        "customer_id": state.get("customer_id"),
        "category": state.get("category"),
        "sentiment": state.get("sentiment"),
        "route_decision": state.get("route"),
        "route_reason": state.get("route_reason"),
        "applied_override": state.get("applied_override"),
        "confidence_score": round(float(state.get("confidence_score", 0.0)), 3),
        "groundedness_score": round(float(state.get("groundedness_score", 0.0)), 3),
        "policy_supported": state.get("policy_supported"),
        "retrieved_sources": state.get("retrieved_sources", []),
        "recheck_loops": state.get("recheck_loops", 0),
        "retrieval_refinements": state.get("retrieval_refinements", 0),
        "draft_reply": draft_dict.get("draft_reply") or state.get("draft_reply"),
        "reviewer_action": draft_dict.get("reviewer_action"),
        "reviewer_comments": draft_dict.get("reviewer_comments"),
        "auto_sent": False,
        "trace": state.get("trace", []),
    }

def summarize_audit_log() -> dict[str, Any]:
    """Read the audit log and produce simple counts for reporting."""
    path = audit_log_path()
    if not path.exists():
        return {"total": 0, "by_route": {}}
    import json

    routes: dict[str, int] = {}
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        total += 1
        r = rec.get("route_decision", "UNKNOWN")
        routes[r] = routes.get(r, 0) + 1
    summary = {"total": total, "by_route": routes}
    write_json(_audit_dir() / "audit_summary.json", summary)
    return summary
