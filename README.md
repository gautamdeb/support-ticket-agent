# Support Ticket Triage & Resolution Agent

An AI support agent that reads customer tickets and, for each one, decides
**Auto-Resolve / Escalate / Refuse / Ask for More Information** and drafts a
reply **for human approval**. Built for the Agentic AI training capstone.

> **Safety principle (hard-wired):** replies are **drafts only and are never
> auto-sent**. Policies are quoted **only** from the knowledge base. If no
> policy is found, the agent says so and **escalates** rather than fabricating.
> Refund-abuse and abusive messages are **refused** with a polite scripted reply.

---

## Stack (mapped to the training's provided accounts)

| Layer | Choice | Why |
|---|---|---|
| LLM | **Groq** (`llama-3.3-70b-versatile`, `openai/gpt-oss-20b`, …) | The training's provided LLM key. OpenAI-compatible. |
| Embeddings | **local `sentence-transformers`** (`all-MiniLM-L6-v2`) | Groq has **no** embeddings API, so we embed locally — no extra key. |
| Vector store | **Chroma** (falls back to an in-memory cosine store) | Local, persistent, inspectable. |
| Orchestration | **LangGraph** (falls back to a built-in runner) | Conditional routing + loops. |
| Evaluation | **Arize AI** (falls back to a local evaluator) | Route/confidence logging + groundedness evaluation. |
| Tracing | **LangSmith** (optional) | Set `LANGCHAIN_TRACING_V2=true`. |
| Web search | **SerpAPI** (optional, **off**) | Conflicts with the KB-only rule; disabled by default. |

**You only need the Groq key to run it for real.** With no keys at all it runs
in a deterministic **mock mode** so you can exercise the whole flow offline.

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env

# Run offline (mock mode) — no keys needed:
python -m src.main --all

# Run for real with Groq:
#   in .env set  LLM_PROVIDER=groq  and  GROQ_API_KEY=...
python -m src.main --all
```

Useful commands:

```bash
python -m src.main                     # sample batch, auto-reviewed
python -m src.main --all               # full 12-ticket synthetic queue
python -m src.main --ticket TCK-1001   # a single ticket
python -m src.main --review cli         # review drafts interactively
python -m src.main --review none        # draft only; leave the HITL queue pending
python -m src.hitl.approval_ui_stub     # open the reviewer console on the queue
python -m src.evaluation.arize_evaluator# run the evaluation report
pytest -q                               # run the test suite (mock mode)
```

---

## The flow

```
Ticket In
  -> Sentiment & Policy Check      (sentiment/abuse + categorise + retrieve + policy check)
  -> RAG Answer Draft              (grounded draft from KB chunks; groundedness + confidence)
  -> LangGraph Route Decision      (base proposal + deterministic safety overrides)
  -> Confidence Re-check Loop      (borderline -> widen retrieval, re-evaluate)
  -> HITL Approval                 (approve / edit / reject / regenerate / escalate)
  -> Audit Log                     (immutable JSONL record; never auto-sends)
```

The route decision is a **base proposal** (LLM or heuristic) followed by
**deterministic overrides** from `config/routing_rules.yaml`, so safety-critical
routing is predictable and auditable regardless of the model.

---

## Project layout

```
config/            app / model / routing_rules YAML
data/
  tickets/         synthetic ticket queue + a small demo batch
  knowledge_base/  Markdown policies & FAQs (the ONLY source of policy)
  evaluation/      golden_dataset.json + expected_routes.json
src/
  graph/           LangGraph state, nodes, edges, support_graph (+ fallback runner)
  agents/          sentiment, rag, policy, triage(router), response
  retrieval/       document loader, chunking, embeddings + vector store, retriever
  memory/          per-customer thread store + conversation memory
  safety/          policy_checker, escalation_rules, abuse_detection, refusal_templates
  hitl/            approval_queue, reviewer_actions, approval_ui_stub (CLI)
  evaluation/      arize_evaluator, route/groundedness/confidence evals
  logging/         audit_logger (JSONL), trace_logger (ReAct-style steps)
  utils/           schemas (pydantic), llm_client (Groq/mock), helpers, constants
notebooks/         RAG, LangGraph flow, and evaluation walkthroughs
tests/             pytest suite (runs fully offline)
outputs/           drafted_replies / audit_logs / evaluation_reports
docs/              architecture, participant guide, rubric, demo script
```

---

## How the safety rules are enforced

- **Never auto-send** — `AUTO_SEND_ALLOWED = False`; every audit record carries
  `auto_sent: false`; approval only marks a draft *ready for a human to send*.
- **KB-only policy** — the RAG agent is instructed to answer *only* from
  retrieved context and cite sources; an **UNKNOWN** category has no policy file
  and always escalates.
- **Documented escalation** — refund-outside-window, 2FA reset, email change,
  etc. are encoded in `safety/escalation_rules.py` straight from the policies.
- **Refuse abuse** — lexical abuse / refund-abuse detection forces `REFUSE`
  with a **scripted** template (never free-form).

---

## Configuration

All behaviour is in `config/*.yaml` and `.env`:

- `config/app_config.yaml` — RAG params (chunk 500–800 tok, overlap 50–100,
  top-k 3–5), confidence thresholds, loop caps, paths.
- `config/model_config.yaml` — provider/model/temperature per agent.
- `config/routing_rules.yaml` — the four routes and the deterministic overrides.

See `docs/architecture.md` for the full design and `docs/participant_guide.md`
for a guided tour.
