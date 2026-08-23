# Architecture

## Overview

The system is a **LangGraph state machine** that processes one ticket at a time.
Each node reads and updates a shared `GraphState` dict and appends to a
ReAct-style trace. The graph enforces the brief's safety principle at every
decision point: it only ever produces a **draft** for a human to approve.

```
                 ┌─────────────────────────┐
   Ticket In ───▶│  sentiment_policy_node   │  sentiment + abuse detection
                 │                          │  categorise
                 │                          │  retrieve KB chunks (RAG steps 1-5)
                 │                          │  policy check + escalation triggers
                 └────────────┬─────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │     rag_answer_node      │  grounded draft from chunks
                 │                          │  groundedness + confidence
                 └────────────┬─────────────┘
                              ▼
                 ┌─────────────────────────┐
                 │   route_decision_node    │  base proposal + safety overrides
                 └────────────┬─────────────┘
                              ▼
                     after_route (conditional)
                     ├── recheck ──▶ recheck_node ──▶ back to sentiment_policy
                     └── compose ──▶ compose_node
                                          ▼
                              ┌────────────────────┐
                              │      HITL queue     │  approve/edit/reject/…
                              └──────────┬──────────┘
                                         ▼
                              ┌────────────────────┐
                              │     audit_node      │  JSONL record (auto_sent=false)
                              └────────────────────┘
```

## Why two graph backends

`support_graph.build_support_graph()` builds a real **LangGraph `StateGraph`**
when `langgraph` is installed, and otherwise a **`FallbackRunner`** that honours
the exact same nodes, edges, conditional branch, and loop-back defined in
`graph/edges.py`. This keeps the project runnable (and testable) with zero heavy
dependencies while remaining a faithful LangGraph implementation in production.

## Decision layering (defence in depth)

1. **LLM / heuristic base proposal** — a first guess at the route.
2. **Deterministic overrides** (`config/routing_rules.yaml`) — always win. They
   encode the non-negotiable safety rules (refuse abuse, escalate when no policy
   or weak grounding, ask when info is missing, escalate documented triggers).
3. **Confidence gate** — `AUTO_RESOLVE` requires confidence ≥ threshold, policy
   support, and adequate grounding; otherwise it degrades to `ESCALATE`.
4. **HITL** — a human still approves before anything is sent.

## Confidence & the re-check loop

Confidence is computed from **discrete signals** (policy support, grounding,
abuse, missing-info, escalation) rather than raw embedding-similarity magnitude,
which differs between the local model and the offline mock embedder. When
confidence lands in the borderline band, the **confidence re-check loop** widens
retrieval (`retrieval_refinements += 1`) and re-evaluates, up to a capped number
of loops, before composing the final draft.

## RAG

`document_loader → chunking (500–800 tok, 50–100 overlap) → embeddings →
vector store → retriever (top 3–5)`. Embeddings are local
(`sentence-transformers`) because Groq serves no embeddings API; Chroma is the
vector store with an in-memory cosine fallback. Groundedness is scored as the
fraction of the draft's content words supported by retrieved context and gates
`AUTO_RESOLVE`.

## Memory

`CustomerThreadStore` persists per-customer interaction history; recording is
idempotent per ticket. `ConversationMemory` merges it with the ticket's own
history so the router can, for example, spot repeated refund requests within
90 days (a refund-abuse signal).

## Evaluation

`arize_evaluator` runs the agent over the golden dataset and reports route
accuracy (with a confusion matrix and per-class precision/recall), confidence
calibration, and groundedness. If Arize credentials are present it also logs
predictions to Arize; otherwise the local offline evaluator writes the report to
`outputs/evaluation_reports/`.

## Safety invariants (enforced in code)

- `constants.AUTO_SEND_ALLOWED = False`; `hitl.auto_send: false` in config.
- Every audit record has `auto_sent: false`.
- Refusals come only from `safety/refusal_templates.py` (never free-form).
- UNKNOWN category ⇒ no policy ⇒ escalate (never fabricate).
