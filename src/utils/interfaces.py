"""Abstract ports the rest of the system depends on.

Concrete adapters (Groq/mock client, Chroma/in-memory store, JSON queue, ...)
satisfy these Protocols structurally, so high-level policy code depends on
behaviour rather than on any specific implementation.
"""
from __future__ import annotations

from typing import Optional, Protocol, Sequence, runtime_checkable

from .schemas import RetrievedChunk, RouteDecision, Ticket


@runtime_checkable
class LanguageModelPort(Protocol):
    @property
    def available(self) -> bool: ...

    def chat(self, system: str, user: str, temperature: float | None = None,
             max_tokens: int | None = None, json_mode: bool = False) -> str: ...

    def chat_json(self, system: str, user: str, temperature: float | None = None) -> dict: ...

    def describe(self) -> str: ...


@runtime_checkable
class EmbeddingPort(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]: ...

    def describe(self) -> str: ...


@runtime_checkable
class VectorStorePort(Protocol):
    def add(self, chunks: Sequence[dict]) -> None: ...

    def query(self, text: str, top_k: int) -> list[RetrievedChunk]: ...

    def count(self) -> int: ...


@runtime_checkable
class RetrieverPort(Protocol):
    def build_index(self) -> int: ...

    def retrieve(self, query: str, category: Optional[str] = None,
                 refinement: int = 0, top_k: Optional[int] = None) -> list[RetrievedChunk]: ...

    def describe(self) -> str: ...


@runtime_checkable
class ConversationMemoryPort(Protocol):
    def refund_requests_last_90d(self, ticket: Ticket) -> int: ...

    def rendered(self, ticket: Ticket) -> str: ...


@runtime_checkable
class ReviewGatePort(Protocol):
    def enqueue(self, draft) -> None: ...

    def list_pending(self) -> list[dict]: ...

    def get(self, ticket_id: str) -> dict | None: ...

    def update(self, record: dict) -> None: ...


@runtime_checkable
class AuditSinkPort(Protocol):
    def __call__(self, record: dict) -> dict: ...


@runtime_checkable
class RoutingRulePort(Protocol):
    """One link in the routing chain: claim a ticket with a RouteDecision, or
    return None to defer to the next rule."""

    name: str

    def evaluate(self, signals: dict) -> Optional[RouteDecision]: ...
