# Demo Script

Roughly 8 minutes. Runs in mock mode; mention Groq where noted.

## Intro (30s)

"This triages support tickets. For each one it picks auto-resolve, escalate,
refuse, or ask for more info, and drafts a reply for a human to approve. It never
sends anything itself, and it only quotes policies that are actually in the
knowledge base."

## Inputs (1 min)

Show `data/tickets/synthetic_tickets.json` (12 tickets across refund,
cancellation, login, troubleshooting, abusive) and `data/knowledge_base/` (the
five policies). "This folder is the only place it's allowed to get policy from."

## Run it (1.5 min)

```
python -m src.main --all
```

Walk a few lines:
- TCK-1001 refund within 7 days, unused -> auto-resolve
- TCK-1002 refund 40 days later -> escalate (past the window)
- TCK-1003 abusive -> refuse
- TCK-1004 "I'll keep asking, still using it daily" -> refuse (refund abuse)
- TCK-1006 lost 2FA -> escalate (needs identity check)
- TCK-1009 "its broken please help" -> ask for more info
- TCK-1010 student discount (no such policy) -> escalate, not invented

## One record (1.5 min)

Open the first line of `outputs/audit_logs/audit_log.jsonl`. Point out the route,
the reason, confidence, groundedness, sources, the step trace, and
`auto_sent: false`.

## Human review (1.5 min)

```
python -m src.hitl.approval_ui_stub
```

Approve one, edit another, escalate a third. "Approving marks it ready to send;
a person still sends it."

## Evaluation (1 min)

```
python -m src.evaluation.arize_evaluator
```

"Accuracy 1.0 against the golden set, no safety violations. With an Arize key it
also logs the run to Arize."

## Real model (30s, optional)

"Set LLM_PROVIDER=groq and a key, and the same flow runs on gpt-oss-20b for the
sentiment, drafting, and routing - the safety rules still apply on top."

## Wrap (30s)

"An LLM proposes, the rules enforce policy, a confidence gate guards
auto-resolve, and a human approves. Nothing is auto-sent and nothing is made up."
