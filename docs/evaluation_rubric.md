# Evaluation Rubric

Maps the brief's final submission checklist to what to look for and where it is.

| # | Requirement | Where | How to verify |
|---|---|---|---|
| 1 | Synthetic ticket queue included | `data/tickets/` | 12 tickets across all 5 categories |
| 2 | Knowledge base files included | `data/knowledge_base/` | 5 Markdown policies/FAQs |
| 3 | LangGraph flow implemented | `src/graph/` | `support_graph.py` builds a `StateGraph`; falls back gracefully |
| 4 | RAG retrieval working | `src/retrieval/` | `pytest tests/test_rag_grounding.py` |
| 5 | Route decision working | `src/agents/triage_agent.py` | 4 routes; `pytest tests/test_routing.py` |
| 6 | HITL approval gate implemented | `src/hitl/` | `pytest tests/test_hitl_flow.py`; `approval_ui_stub` |
| 7 | Customer memory implemented | `src/memory/` | repeated-refund detection; idempotent recording |
| 8 | Confidence re-check loop | `src/graph/nodes.py` (`after_route`, `recheck_node`) | borderline confidence widens retrieval |
| 9 | Audit logs generated | `outputs/audit_logs/audit_log.jsonl` | one record/ticket, `auto_sent: false` |
| 10 | Evaluation report generated | `outputs/evaluation_reports/` | `python -m src.evaluation.arize_evaluator` |
| 11 | Demo script included | `docs/demo_script.md` | — |
| 12 | README setup instructions | `README.md` | — |

## Quality bars

- **Route accuracy** ≥ 0.8 vs `expected_routes.json` (target in
  `app_config.yaml`). Current mock-mode baseline: **1.0**.
- **Safety:** zero `AUTO_RESOLVE` below the confidence threshold; zero
  `auto_sent: true`; abusive/refund-abuse → `REFUSE`; unknown policy → `ESCALATE`.
- **Grounding:** `AUTO_RESOLVE` drafts cite KB sources and score above the
  groundedness pass threshold.

## Scoring suggestion (100 pts)

- Correct 4-way routing on the golden set — 30
- RAG grounding + citations + KB-only discipline — 20
- HITL gate + reviewer actions + never-auto-send — 20
- Safety (abuse refusal, no-policy escalation, escalation triggers) — 15
- Evaluation report + audit trail quality — 10
- Code clarity, config-driven design, tests — 5
