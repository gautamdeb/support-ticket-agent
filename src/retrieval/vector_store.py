from __future__ import annotations

import hashlib
import math
import re
from typing import Optional

from ..utils.helpers import env, model_config
from ..utils.schemas import RetrievedChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")

def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())

class Embedder:
    def __init__(self) -> None:
        cfg = model_config().get("embeddings", {})
        self.provider = env("EMBEDDINGS_PROVIDER", cfg.get("provider", "mock")).lower()
        self.model_name = env("EMBEDDINGS_MODEL", cfg.get("model", "all-MiniLM-L6-v2"))
        self.dimension = int(cfg.get("dimension", 384))
        self._st_model = None
        if self.provider == "local":
            self._init_local()

    def _init_local(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer(self.model_name)
            get_dim = getattr(self._st_model, "get_embedding_dimension", None) \
                or self._st_model.get_sentence_embedding_dimension
            self.dimension = get_dim()
        except Exception:
            self.provider = "mock"

    def _mock_embed_one(self, text: str, dim: int = 512) -> list[float]:
        """Hashing bag-of-words vector with L2 normalisation."""
        vec = [0.0] * dim
        for tok in _tokenize(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.provider == "local" and self._st_model is not None:
            return [list(map(float, v)) for v in self._st_model.encode(texts)]
        return [self._mock_embed_one(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def describe(self) -> str:
        return f"{self.provider}:{self.model_name if self.provider == 'local' else 'hash-bow'}"

def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)

class MemoryVectorStore:
    """Pure-python cosine store."""

    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self._chunks: list[dict] = []
        self._vectors: list[list[float]] = []

    def add(self, chunks: list[dict]) -> None:
        vecs = self.embedder.embed([c["text"] for c in chunks])
        self._chunks.extend(chunks)
        self._vectors.extend(vecs)

    def query(self, text: str, top_k: int) -> list[RetrievedChunk]:
        if not self._chunks:
            return []
        q = self.embedder.embed_one(text)
        scored = [
            (cosine(q, v), c) for v, c in zip(self._vectors, self._chunks)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, c in scored[:top_k]:
            out.append(
                RetrievedChunk(
                    text=c["text"], source=c["source"],
                    score=round(float(score), 4), chunk_index=c.get("chunk_index", 0),
                )
            )
        return out

    def count(self) -> int:
        return len(self._chunks)

class ChromaVectorStore:
    """Persistent Chroma-backed store."""

    def __init__(self, embedder: Embedder, persist_dir: str) -> None:
        import chromadb

        self.embedder = embedder
        self._client = chromadb.PersistentClient(path=persist_dir)
        try:
            self._client.delete_collection("kb")
        except Exception:
            pass
        self._col = self._client.create_collection("kb")

    def add(self, chunks: list[dict]) -> None:
        vecs = self.embedder.embed([c["text"] for c in chunks])
        self._col.add(
            ids=[f"{c['source']}::{c['chunk_index']}" for c in chunks],
            embeddings=vecs,
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks],
        )

    def query(self, text: str, top_k: int) -> list[RetrievedChunk]:
        q = self.embedder.embed_one(text)
        res = self._col.query(query_embeddings=[q], n_results=top_k)
        out: list[RetrievedChunk] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[None] * len(docs)])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            score = 1.0 - float(dist) if dist is not None else 0.0
            out.append(
                RetrievedChunk(
                    text=doc, source=meta.get("source", "unknown"),
                    score=round(score, 4), chunk_index=int(meta.get("chunk_index", 0)),
                )
            )
        return out

    def count(self) -> int:
        try:
            return self._col.count()
        except Exception:
            return 0

def build_vector_store(embedder: Optional[Embedder] = None):
    """Factory: chroma if requested & available, else memory."""
    embedder = embedder or Embedder()
    backend = env("VECTOR_STORE", "memory").lower()
    if backend == "chroma":
        try:
            persist = env("CHROMA_PERSIST_DIR", "./data/.chroma")
            return ChromaVectorStore(embedder, persist)
        except Exception:
            return MemoryVectorStore(embedder)
    return MemoryVectorStore(embedder)
