"""RAG retrieval, chunking and groundedness."""
from src.evaluation.groundedness_eval import groundedness_score
from src.retrieval.chunking import chunk_documents
from src.retrieval.document_loader import load_documents
from src.retrieval.retriever import get_retriever

def test_documents_load():
    docs = load_documents()
    sources = {d["source"] for d in docs}
    assert "refund_policy.md" in sources
    assert len(docs) >= 5

def test_chunking_produces_chunks():
    docs = load_documents()
    chunks = chunk_documents(docs)
    assert len(chunks) >= len(docs)
    for c in chunks:
        assert c["text"].strip()
        assert "source" in c

def test_retriever_finds_refund_policy():
    r = get_retriever()
    chunks = r.retrieve("refund within 7 days of billing",
                        category="refund_request")
    assert any(c.source == "refund_policy.md" for c in chunks)

def test_groundedness_high_for_quoted_text():
    context = ["Customers are eligible for a refund within 7 days of billing."]
    grounded = "You are eligible for a refund within 7 days of billing."
    assert groundedness_score(grounded, context) > 0.6

def test_groundedness_low_for_unrelated_text():
    context = ["Customers are eligible for a refund within 7 days of billing."]
    ungrounded = "Penguins migrate across Antarctic glaciers during winter storms."
    assert groundedness_score(ungrounded, context) < 0.3
