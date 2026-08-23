# Demo Script (~8 minutes)

A walkthrough you can present live. Runs in mock mode; mention Groq where noted.

## 0. Framing (30s)
"This is a support triage agent. For every ticket it decides one of four
actions — Auto-Resolve, Escalate, Refuse, Ask for More Info — and drafts a reply
**for a human to approve**. It never sends anything itself, and it only quotes
policies that exist in our knowledge base."

## 1. Show the inputs (1 min)
- `data/tickets/synthetic_tickets.json` — 12 tickets across refund, cancellation,
  login, troubleshooting, abusive.
- `data/knowledge_base/` — the 5 Markdown policies. "This is the ONLY place the
  agent is allowed to get policy from."

## 2. Run the full queue (1.5 min)
```bash
python -m src.main --all
```
Talk through the output line by line:
- `TCK-1001` refund **within** 7 days, unused → **AUTO_RESOLVE**.
- `TCK-1002` refund **40 days** later → **ESCALATE** (outside the window).
- `TCK-1003` abusive → **REFUSE** (scripted).
- `TCK-1004` "I'll keep requesting… still using it daily" → **REFUSE** (refund abuse).
- `TCK-1006` lost 2FA device → **ESCALATE** (needs identity verification).
- `TCK-1009` "its broken please help" → **ASK_MORE_INFO**.
- `TCK-1010` student discount (no such policy) → **ESCALATE**, not invented.

## 3. Open one draft + audit record (1.5 min)
```bash
head -n 1 outputs/audit_logs/audit_log.jsonl | python -m json.tool
```
Point out `route_reason`, `applied_override`, `confidence_score`,
`groundedness_score`, `retrieved_sources`, the `trace`, and `auto_sent: false`.

## 4. Human-in-the-loop (1.5 min)
```bash
python -m src.hitl.approval_ui_stub
```
Approve one, **edit** another, **escalate** a third. "Approving marks it ready
to send — a person still sends it through an approved channel."

## 5. Evaluation (1 min)
```bash
python -m src.evaluation.arize_evaluator
cat outputs/evaluation_reports/evaluation_report.md
```
"Route accuracy 1.0 against our golden set; zero safety violations. With an
Arize key this also streams to Arize for online monitoring."

## 6. Switch to the real model (30s, optional)
"Set `LLM_PROVIDER=groq` and a `GROQ_API_KEY`, and the same graph now uses
`llama-3.3-70b-versatile` on Groq for the sentiment, drafting, and routing steps
— the deterministic safety overrides still apply on top."

## 7. Close (30s)
"Defence in depth: an LLM proposes, deterministic rules enforce policy, a
confidence gate guards auto-resolve, and a human approves. Nothing is ever
auto-sent, and nothing is ever fabricated."
