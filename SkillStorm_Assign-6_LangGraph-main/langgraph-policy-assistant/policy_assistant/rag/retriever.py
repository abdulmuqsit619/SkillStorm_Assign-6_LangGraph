from pathlib import Path
from functools import lru_cache

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from policy_assistant import config


DOCUMENT_DIR = Path(__file__).resolve().parent.parent.parent / "documents"

@lru_cache(maxsize=1)
def build_vector_store() -> InMemoryVectorStore:
    chunks = load_document_chunks()

    embeddings = BedrockEmbeddings(
        model_id=config.BEDROCK_EMBED_MODEL_ID,
        region_name=config.AWS_REGION,
    )

    store = InMemoryVectorStore.from_documents(
        chunks,
        embeddings,
    )

    return store


def load_document_chunks() -> list[Document]:
    splitter = MarkdownHeaderTextSplitter(
        [
            ("#", "title"),
            ("##", "section"),
        ],
        strip_headers=False,
    )

    chunks: list[Document] = []

    for path in sorted(DOCUMENT_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")

        for chunk in splitter.split_text(text):
            chunk.metadata["source"] = path.name
            chunks.append(chunk)

    return chunks


def retrieve_documents(query: str, k: int = 4) -> list[Document]:
    store = build_vector_store()

    return store.similarity_search(
        query,
        k=k,
    )