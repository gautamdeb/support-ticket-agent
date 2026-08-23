"""Declarative edge specification, shared by both graph builders."""
from __future__ import annotations

from . import nodes

ENTRY = "sentiment_policy"

NODES = {
    "sentiment_policy": nodes.sentiment_policy_node,
    "rag_answer": nodes.rag_answer_node,
    "route_decision": nodes.route_decision_node,
    "recheck": nodes.recheck_node,
    "compose": nodes.compose_node,
    "audit": nodes.audit_node,
}

LINEAR_EDGES = {
    "sentiment_policy": "rag_answer",
    "rag_answer": "route_decision",
    "recheck": "sentiment_policy",
    "compose": "audit",
}

CONDITIONAL_EDGES = {
    "route_decision": (nodes.after_route, {"recheck": "recheck", "compose": "compose"}),
}

TERMINAL = "audit"
