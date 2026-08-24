# Support Ticket Triage & Resolution Agent

An agent that reads a support ticket and decides what to do with it:
auto-resolve, escalate, refuse, or ask for more info. It drafts the reply but
never sends anything - a human approves first. Policy answers only come from the
knowledge base; if there's no policy for something, it escalates instead of
making something up.

Built as the capstone for the Agentic AI training.

## What it uses

- Groq for the LLM (sentiment, drafting, the routing decision)
- sentence-transformers for embeddings (Groq doesn't do embeddings, so these run
  locally - no extra key needed)
- Chroma for the vector store (falls back to an in-memory one if Chroma isn't
  installed)
- LangGraph for the flow (there's a plain fallback runner too, so it still works
  without langgraph)
- Arize for the evaluation logging

You only need a Groq key to actually run it. Add an Arize key when you want the
eval pushed to the dashboard. With no keys at all it runs in a mock mode that's
handy for tests.

## Setup

```
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # then edit .env
```

In `.env` set at least:

```
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=openai/gpt-oss-20b
EMBEDDINGS_PROVIDER=local
VECTOR_STORE=chroma
```

Add `ARIZE_API_KEY` and `ARIZE_SPACE_ID` if you want evaluation logged to Arize.

## Running it

```
python -m src.main                    # sample batch
python -m src.main --all              # full 12-ticket queue
python -m src.main --ticket TCK-1001  # one ticket
python -m src.main --review cli        # review the drafts yourself
python -m src.evaluation.arize_evaluator   # score against the golden set
python -m src.hitl.approval_ui_stub    # open the reviewer console
pytest                                 # run the tests (no keys needed)
```

`diagnose_groq.py` is a small helper that checks your key works and lists the
models it can reach - run `python diagnose_groq.py` if the model call fails.

## The flow

```
Ticket -> sentiment & policy check -> RAG draft -> route decision
       -> confidence re-check loop -> human approval -> audit log
```

The route decision starts from the LLM (or a keyword fallback) and then goes
through a set of rules that enforce the hard requirements: abuse gets a scripted
refusal, no policy means escalate, missing details means ask, and auto-resolve
only fires when the answer is grounded and confident enough.

## Layout

```
config/            app / model / routing settings
data/
  tickets/         the synthetic ticket queue
  knowledge_base/  the markdown policies and FAQs
  evaluation/      golden routes + dataset
src/
  graph/           LangGraph state, nodes, edges, graph builder
  agents/          sentiment, rag, policy, triage, response, routing rules
  retrieval/       loader, chunking, embeddings + vector store, retriever
  memory/          per-customer thread store
  safety/          policy check, escalation triggers, abuse detection, refusals
  hitl/            approval queue, reviewer actions, review console
  evaluation/      route / groundedness / confidence eval + Arize logging
  logging/         audit log + step trace
  utils/           schemas, llm client, interfaces, container, helpers
tests/             pytest suite
docs/              architecture, participant guide, rubric, demo script
```

## Safety rules

Nothing is ever auto-sent - approval only marks a draft ready for a person to
send. Refusals come from fixed templates, not the model. An unknown category has
no policy, so it escalates. These are enforced in the routing rules, not left to
the model to remember.

More detail in `docs/architecture.md`.
