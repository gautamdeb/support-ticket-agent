"""High-level retriever: builds the index and serves top-k chunks."""
from __future__ import annotations

from typing import Optional

from ..utils.constants import CATEGORY_TO_POLICY_FILES
from ..utils.helpers import app_config
from ..utils.schemas import RetrievedChunk
from .chunking import chunk_documents
from .document_loader import load_documents
from .vector_store import Embedder, build_vector_store

_CATEGORY_KEYWORDS = {
    "refund_request": "refund eligibility 7 day window billing renewal escalate",
    "subscription_cancellation": "cancel subscription auto-renew manage plan billing",
    "login_account_access": "password reset login locked 2FA identity verification email",
    "product_troubleshooting": "error blank screen sync export refresh cache browser",
    "abusive_message": "abusive threatening refusal refund abuse policy",
}

class Retriever:
    def __init__(self) -> None:
        self.embedder = Embedder()
        self.store = build_vector_store(self.embedder)
        self._built = False

    def build_index(self) -> int:
        docs = load_documents()
        chunks = chunk_documents(docs)
        self.store.add(chunks)
        self._built = True
        return len(chunks)

    def ensure_built(self) -> None:
        if not self._built:
            self.build_index()

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        refinement: int = 0,
        top_k: Optional[int] = None,
    ) -> list[RetrievedChunk]:
        self.ensure_built()
        cfg = app_config()["rag"]
        k = top_k or cfg["top_k"]
        expanded = query
        if refinement > 0 and category in _CATEGORY_KEYWORDS:
            expanded = f"{query}\n{_CATEGORY_KEYWORDS[category]}"
            k = min(k + 2 * refinement, 8)
        results = self.store.query(expanded, top_k=k)
        min_score = cfg["min_relevance_score"]
        return [r for r in results if r.score >= min_score] or results[:1]

    def describe(self) -> str:
        return f"embedder={self.embedder.describe()} store={type(self.store).__name__} chunks={self.store.count()}"

_SINGLETON: Optional[Retriever] = None

def get_retriever() -> Retriever:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = Retriever()
        _SINGLETON.build_index()
    return _SINGLETON
