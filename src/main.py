"""Entry point: run the Support Ticket Triage & Resolution Agent over a queue."""
from __future__ import annotations

import argparse
from typing import Any

from .graph.graph_state import init_state
from .hitl.reviewer_actions import apply_reviewer_action, auto_review
from .logging.audit_logger import summarize_audit_log
from .logging.trace_logger import TraceLogger
from .utils.container import ServiceContainer
from .utils.helpers import app_config, project_path, read_json, write_json
from .utils.schemas import Ticket

def _load_tickets(path: str) -> list[Ticket]:
    return [Ticket(**t) for t in read_json(path)]

def run_pipeline(
    tickets: list[Ticket],
    review_mode: str = "auto",
    verbose: bool = True,
    container: ServiceContainer | None = None,
) -> list[dict[str, Any]]:
    """Run every ticket through the graph and return the final HITL records.

    Collaborators are supplied by the composition root; a caller (e.g. a test)
    may inject its own container to substitute providers.
    """
    container = container or ServiceContainer.build()
    graph = container.flow
    queue = container.review_gate

    if verbose:
        print(container.banner())
        print(f"Processing {len(tickets)} ticket(s)...  [auto_send=False - drafts only]\n")

    results: list[dict[str, Any]] = []
    for ticket in tickets:
        tracer = TraceLogger(ticket.ticket_id)
        state = init_state(ticket, {
            "client": container.language_model, "retriever": container.retriever,
            "memory": container.memory, "tracer": tracer,
        })
        final = graph.invoke(state)
        draft = final["draft"]
        queue.enqueue(draft)

        if review_mode == "auto":
            action, comments = auto_review(draft.model_dump())
            record = apply_reviewer_action(queue, ticket.ticket_id, action, comments)
        else:
            record = queue.get(ticket.ticket_id)

        results.append(record)
        if verbose:
            print(f"  {ticket.ticket_id}: {record['route_decision']:<13} "
                  f"conf={record['confidence_score']:<5} "
                  f"grounded={record.get('groundedness_score')} "
                  f"reviewer={record.get('reviewer_action')} "
                  f"sources={record.get('retrieved_sources')}")

    out = project_path(app_config()["paths"]["drafted_replies"], "drafted_replies.json")
    write_json(out, results)

    if review_mode == "cli":
        from .hitl.approval_ui_stub import run_console
        print("\nLaunching reviewer console...\n")
        run_console()

    summary = summarize_audit_log()
    if verbose:
        print(f"\nAudit summary: {summary}")
        print(f"Drafts written to: {out}")
    return results

def main() -> None:
    parser = argparse.ArgumentParser(description="Support Ticket Triage & Resolution Agent")
    parser.add_argument("--all", action="store_true", help="run the full synthetic ticket queue")
    parser.add_argument("--ticket", type=str, help="run a single ticket id from the full queue")
    parser.add_argument("--review", choices=["auto", "cli", "none"], default="auto",
                        help="how to handle the HITL approval step")
    parser.add_argument("--limit", type=int, default=0, help="limit number of tickets")
    args = parser.parse_args()

    paths = app_config()["paths"]
    src = paths["tickets"] if (args.all or args.ticket) else paths["ticket_batch"]
    tickets = _load_tickets(project_path(src))

    if args.ticket:
        tickets = [t for t in tickets if t.ticket_id == args.ticket]
        if not tickets:
            print(f"Ticket {args.ticket} not found in {src}")
            return
    if args.limit:
        tickets = tickets[: args.limit]

    run_pipeline(tickets, review_mode=args.review)

if __name__ == "__main__":
    main()
