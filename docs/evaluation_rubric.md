# Evaluation Rubric

Maps the submission checklist to where each piece lives and how to check it.

| Requirement | Where | Check |
|---|---|---|
| Synthetic ticket queue | `data/tickets/` | 12 tickets across the 5 categories |
| Knowledge base | `data/knowledge_base/` | 5 markdown policies/FAQs |
| LangGraph flow | `src/graph/` | `support_graph.py` builds the StateGraph |
| RAG retrieval | `src/retrieval/` | `pytest tests/test_rag_grounding.py` |
| Route decision | `src/agents/` | 4 routes; `pytest tests/test_routing.py` |
| HITL approval gate | `src/hitl/` | `pytest tests/test_hitl_flow.py` |
| Customer memory | `src/memory/` | repeated-refund detection |
| Confidence re-check loop | `src/graph/nodes.py`, `after_route` | borderline confidence widens retrieval |
| Audit logs | `outputs/audit_logs/audit_log.jsonl` | one record per ticket, `auto_sent: false` |
| Evaluation report | `outputs/evaluation_reports/` | `python -m src.evaluation.arize_evaluator` |
| Demo script | `docs/demo_script.md` | - |
| README | `README.md` | - |

## Bars

- Route accuracy at least 0.8 against `expected_routes.json` (target is in
  `app_config.yaml`). Current baseline is 1.0.
- No auto-resolve below the confidence floor; no `auto_sent: true`; abuse ->
  refuse; unknown policy -> escalate.
- Auto-resolve drafts cite their KB sources.

## Suggested scoring (100)

- 4-way routing correct on the golden set: 30
- RAG grounding + citations + KB-only answers: 20
- HITL gate + reviewer actions + never-auto-send: 20
- Safety (abuse refusal, no-policy escalation, escalation triggers): 15
- Evaluation report + audit trail: 10
- Code clarity + tests: 5
