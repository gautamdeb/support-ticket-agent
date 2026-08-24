# Participant Guide

A quick walkthrough. You can do all of it in mock mode without any keys; add the
Groq key when you want the real model.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

For a real run, set `LLM_PROVIDER=groq` and your `GROQ_API_KEY` in `.env`
(get the key from console.groq.com). Otherwise leave it and it runs in mock mode.

## Run the queue

```
python -m src.main --all
```

You'll get one line per ticket with the route, confidence, groundedness, the
reviewer's action, and which sources were used. Drafts land in
`outputs/drafted_replies/` and the audit trail in `outputs/audit_logs/`.

## Review the drafts

```
python -m src.main --review none      # draft only, don't auto-review
python -m src.hitl.approval_ui_stub   # then approve / edit / reject / escalate
```

Approving just marks a draft ready - nothing goes to a customer.

## Look at one audit record

```
python -c "import json;print(json.dumps([json.loads(l) for l in open('outputs/audit_logs/audit_log.jsonl')][0], indent=2))"
```

Note the route, the reason, confidence, groundedness, sources, the step trace,
and `auto_sent: false`.

## Evaluate

```
python -m src.evaluation.arize_evaluator
```

Prints route accuracy against `data/evaluation/expected_routes.json` and writes
the report to `outputs/evaluation_reports/`.

## Things to try

- Swap the model with `GROQ_MODEL=openai/gpt-oss-120b` and re-run.
- Add a ticket whose answer isn't in the KB and check it escalates.
- Change `auto_resolve_min_confidence` in `config/app_config.yaml` and watch the
  auto-resolve/escalate split move.
- Drop a new policy `.md` into `data/knowledge_base/`, add a matching ticket, and
  see it retrieved and cited.

## Where to change things

- routing logic: `src/agents/routing_rules.py`
- RAG settings: `config/app_config.yaml`
- prompts: the `_SYSTEM` strings in `src/agents/`
- refusal wording: `src/safety/refusal_templates.py`
- escalation triggers: `src/safety/escalation_rules.py`
- knowledge base: `data/knowledge_base/`
- tickets: `data/tickets/`
