from policy_assistant.rag.retriever import (
    load_document_chunks,
)


def test_documents_load():
    chunks = load_document_chunks()

    assert len(chunks) > 0


def test_chunks_have_sources():
    chunks = load_document_chunks()

    assert all(
        "source" in chunk.metadata
        for chunk in chunks
    )


def test_expected_documents_loaded():
    chunks = load_document_chunks()

    sources = {
        chunk.metadata["source"]
        for chunk in chunks
    }

    assert "refund-policy.md" in sources
    assert "shipping-policy.md" in sources
    assert "account-and-billing.md" in sources