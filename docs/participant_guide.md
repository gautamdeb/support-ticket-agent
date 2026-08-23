# Participant Guide

A guided tour for the capstone. Follow it top to bottom.

## 1. Set up

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

You can do the entire walkthrough in **mock mode** (no keys). To use the real
LLM, set in `.env`: `LLM_PROVIDER=groq` and `GROQ_API_KEY=...` (from
https://console.groq.com/keys). Get the Groq key from the training's
"Agentic AI Training Readiness" doc.

## 2. Run the pipeline

```bash
python -m src.main --all
```

You'll see one line per ticket: its route, confidence, groundedness, the
reviewer's action, and the sources retrieved. Drafts are written to
`outputs/drafted_replies/` and an audit trail to `outputs/audit_logs/`.

## 3. Review drafts like a human would

```bash
python -m src.main --review none     # draft everything, don't auto-review
python -m src.hitl.approval_ui_stub  # then approve / edit / reject / escalate
```

Nothing is ever sent to a customer — approval only marks a draft **ready** to
send.

## 4. Read one audit record

```bash
head -n 1 outputs/audit_logs/audit_log.jsonl | python -m json.tool
```

Note `route_decision`, `route_reason`, `applied_override`, `confidence_score`,
`groundedness_score`, `retrieved_sources`, and the `trace` (the step-by-step
reasoning path). Every record has `auto_sent: false`.

## 5. Evaluate

```bash
python -m src.evaluation.arize_evaluator
cat outputs/evaluation_reports/evaluation_report.md
```

Compare the agent's routes to `data/evaluation/expected_routes.json`.

## 6. Things to try (suggested exercises)

- **Swap the model.** Set `GROQ_MODEL=openai/gpt-oss-20b` and re-run. Does route
  accuracy hold?
- **Break grounding.** Add a ticket whose answer isn't in the KB. Confirm it
  escalates rather than fabricating.
- **Tune thresholds.** Change `auto_resolve_min_confidence` in
  `config/app_config.yaml` and watch AUTO_RESOLVE vs ESCALATE shift.
- **Add a policy.** Drop a new `*.md` into `data/knowledge_base/`, add a ticket,
  and see it retrieved and cited.
- **Add an eval case.** Extend `data/evaluation/expected_routes.json` and the
  golden dataset, then re-run the evaluator.
- **Turn on Arize.** Add `ARIZE_API_KEY` + `ARIZE_SPACE_ID` and re-run to log
  predictions.

## 7. Where things live

| You want to change… | Edit… |
|---|---|
| Routing rules / overrides | `config/routing_rules.yaml`, `src/agents/triage_agent.py` |
| RAG params | `config/app_config.yaml` (`rag:`) |
| The prompts | `src/agents/*.py` (the `_SYSTEM` strings) |
| Refusal wording | `src/safety/refusal_templates.py` |
| Escalation triggers | `src/safety/escalation_rules.py` |
| The KB | `data/knowledge_base/*.md` |
| The tickets | `data/tickets/*.json` |
