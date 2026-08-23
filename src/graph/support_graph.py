"""Build the support agent graph."""
from __future__ import annotations

from typing import Any

from . import edges
from .graph_state import GraphState

class FallbackRunner:
    """Minimal deterministic executor mirroring the LangGraph wiring."""

    def __init__(self, max_steps: int = 30) -> None:
        self.max_steps = max_steps
        self.backend = "fallback"

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        current = edges.ENTRY
        steps = 0
        while current is not None and steps < self.max_steps:
            steps += 1
            fn = edges.NODES[current]
            updates = fn(state) or {}
            state.update(updates)

            if current in edges.CONDITIONAL_EDGES:
                router_fn, mapping = edges.CONDITIONAL_EDGES[current]
                branch = router_fn(state)
                current = mapping.get(branch)
                continue
            if current == edges.TERMINAL:
                break
            current = edges.LINEAR_EDGES.get(current)
        return state

def _build_langgraph():
    from langgraph.graph import END, StateGraph

    g = StateGraph(GraphState)
    for name, fn in edges.NODES.items():
        g.add_node(name, fn)
    g.set_entry_point(edges.ENTRY)

    for src, dst in edges.LINEAR_EDGES.items():
        g.add_edge(src, dst)
    for src, (router_fn, mapping) in edges.CONDITIONAL_EDGES.items():
        g.add_conditional_edges(src, router_fn, mapping)
    g.add_edge(edges.TERMINAL, END)

    compiled = g.compile()
    compiled.backend = "langgraph"
    return compiled

def build_support_graph(prefer_langgraph: bool = True):
    if prefer_langgraph:
        try:
            return _build_langgraph()
        except Exception:
            pass
    return FallbackRunner()
