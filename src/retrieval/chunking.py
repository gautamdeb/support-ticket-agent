"""Token-aware chunking."""
from __future__ import annotations

from ..utils.helpers import app_config, estimate_tokens

def _split_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n")]
    return [p for p in paras if p]

def chunk_document(source: str, text: str,
                   chunk_size_tokens: int | None = None,
                   overlap_tokens: int | None = None) -> list[dict]:
    cfg = app_config()["rag"]
    chunk_size = chunk_size_tokens or cfg["chunk_size_tokens"]
    overlap = overlap_tokens or cfg["chunk_overlap_tokens"]

    paragraphs = _split_paragraphs(text)
    chunks: list[dict] = []
    current: list[str] = []
    current_tokens = 0
    idx = 0

    def flush() -> list[str]:
        nonlocal current, current_tokens, idx
        if not current:
            return []
        chunk_text = "\n\n".join(current)
        chunks.append({"source": source, "text": chunk_text, "chunk_index": idx})
        idx += 1
        tail: list[str] = []
        tail_tokens = 0
        for para in reversed(current):
            t = estimate_tokens(para)
            if tail_tokens + t > overlap:
                break
            tail.insert(0, para)
            tail_tokens += t
        return tail

    for para in paragraphs:
        ptok = estimate_tokens(para)
        if current_tokens + ptok > chunk_size and current:
            carry = flush()
            current = list(carry)
            current_tokens = sum(estimate_tokens(p) for p in current)
        current.append(para)
        current_tokens += ptok

    flush()
    return chunks

def chunk_documents(docs: list[dict]) -> list[dict]:
    out: list[dict] = []
    for d in docs:
        out.extend(chunk_document(d["source"], d["text"]))
    return out
