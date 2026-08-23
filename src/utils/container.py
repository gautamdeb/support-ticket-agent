"""Composition root.

The one place the object graph is assembled: concrete adapters are chosen here
and handed to collaborators, so every other module depends only on the ports in
`interfaces.py`. Swapping a provider or store is a change confined to this file.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..graph.support_graph import build_support_graph
from ..hitl.approval_queue import ApprovalQueue
from ..memory.conversation_memory import ConversationMemory
from ..memory.customer_thread_store import CustomerThreadStore
from ..retrieval.retriever import Retriever
from .helpers import load_dotenv_if_present
from .interfaces import (
    ConversationMemoryPort, LanguageModelPort, RetrieverPort, ReviewGatePort,
)
from .llm_client import get_llm_client


@dataclass
class ServiceContainer:
    language_model: LanguageModelPort
    retriever: RetrieverPort
    memory: ConversationMemoryPort
    review_gate: ReviewGatePort
    flow: Any
    indexed_chunks: int

    @classmethod
    def build(cls) -> "ServiceContainer":
        load_dotenv_if_present()
        retriever = Retriever()
        indexed = retriever.build_index()
        return cls(
            language_model=get_llm_client(),
            retriever=retriever,
            memory=ConversationMemory(CustomerThreadStore()),
            review_gate=ApprovalQueue(),
            flow=build_support_graph(),
            indexed_chunks=indexed,
        )

    def banner(self) -> str:
        return (f"LLM: {self.language_model.describe()}\n"
                f"Retriever: {self.retriever.describe()} "
                f"(indexed {self.indexed_chunks} chunks)\n"
                f"Graph backend: {getattr(self.flow, 'backend', 'unknown')}")
