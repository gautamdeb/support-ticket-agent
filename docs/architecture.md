# Architecture

The system processes one ticket at a time through a LangGraph state machine.
Each node reads and updates a shared state dict and appends to a step trace. The
whole thing only ever produces a draft for a human to approve.

## Flow

```
Ticket in
  -> sentiment_policy   (sentiment + abuse check, categorise, retrieve, policy check)
  -> rag_answer         (draft an answer from the retrieved chunks)
  -> route_decision     (pick one of the four routes)
  -> [re-check?]        (borderline confidence -> widen retrieval, try again)
  -> compose            (build the final draft)
  -> audit              (write the record; never sends)
```

If langgraph is installed the flow runs as a compiled StateGraph. If it isn't,
a small fallback runner walks the same nodes and edges. Both are wired from the
same definitions in `graph/edges.py`, so they behave identically.

## Routing

The route decision has two parts. First the LLM (or a keyword fallback when
there's no key) proposes something and confidence is scored from the signals.
Then a RuleBook runs a chain of typed rules in priority order and the first one
that matches wins:

1. abusive content -> refuse
2. refund abuse -> refuse
3. documented escalation trigger (refund past 7 days, 2FA reset, email change) -> escalate
4. missing details -> ask for more info
5. no governing policy -> escalate
6. weak grounding -> escalate
7. confident and grounded -> auto-resolve
8. otherwise -> escalate

The rules are plain Python classes (`agents/routing_rules.py`), not string
expressions, so the routing is easy to read and test and there's nothing to
mis-evaluate.

## Confidence

Confidence comes from the decision signals (policy found, grounded, abuse,
missing info, escalation), not from raw embedding similarity, because the
similarity scale differs between the real embedding model and the mock one used
in tests. When confidence lands in the middle band the re-check loop widens
retrieval and re-runs the analysis a couple of times before settling.

## RAG

Documents are loaded from `data/knowledge_base`, chunked (~500-800 tokens with
overlap), embedded, and stored. Embeddings run locally through
sentence-transformers because Groq has no embeddings endpoint. Chroma is the
store, with an in-memory cosine store as the fallback. Groundedness is the share
of the draft's words that appear in the retrieved text; it gates auto-resolve.

## Memory

`customer_thread_store.py` keeps a per-customer history so the agent can spot
repeated refund requests inside 90 days (one of the refund-abuse signals).
Recording is keyed by ticket id, so re-running the same batch doesn't inflate the
counts.

## Evaluation

`evaluation/` scores the routes against the golden set (accuracy, a confusion
matrix, per-class precision/recall), checks confidence calibration, and averages
groundedness. If Arize keys are set it also logs the run to Arize; otherwise it
just writes the local report to `outputs/evaluation_reports/`.

## Where the safety rules live

- Never auto-send: the audit record always carries `auto_sent: false`, and
  approval only marks a draft ready to send.
- Refusals: fixed templates in `safety/refusal_templates.py`.
- No fabrication: an unknown category has no policy file, so it escalates.
- Escalation triggers: `safety/escalation_rules.py`, taken straight from the
  policy docs.

## Composition

`utils/container.py` builds the objects and wires them together in one place;
everything else depends on the small interfaces in `utils/interfaces.py` rather
than on concrete classes. Swapping the LLM, the store, or the queue is a change
in the container only.
