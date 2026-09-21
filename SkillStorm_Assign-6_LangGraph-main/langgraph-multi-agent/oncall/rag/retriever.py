""" Create a retreiver we can use as part of our chains for RAG """


from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_aws import AmazonKnowledgeBasesRetriever, BedrockEmbeddings

from functools import lru_cache
from .. import config
from pathlib import Path


RUNBOOK_DIR = Path(__file__).resolve().parent.parent.parent / "runbooks"


def load_runbook_chunks() -> list[Document]:
    """ read runbooks/*.md and split each by its "#" and "##" headings """

    splitter = MarkdownHeaderTextSplitter(
        [("#", "title"), ("##", "section")],
        strip_headers=False     # keep the header text inside of the chunks
    )

    chunks: list[Document] = []
    for path in sorted(RUNBOOK_DIR.glob("*.md")):
        for chunk in splitter.split_text(path.read_text(encoding="utf-8")):
            chunk.metadata["source"] = path.name
            chunks.append(chunk)

    return chunks


class ScoreThresholdRetriever(BaseRetriever):
    "Top-k and Top-p retrieval of documents"

    store: InMemoryVectorStore
    k: int = 4
    threshold: float = 0.40

    # InMemoryVectorStore is not a type Pydantic will recognize, so we need to tell Pydantic to allow it
    model_config = {"arbitrary_types_allowed": True}

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:

        # find the K most relevant documents
        hits = self.store.similarity_search_with_score(query, k=self.k)

        # filter out only the docs that meet our threshold minimum
        return [doc for doc, score in hits if score >= self.threshold]


@lru_cache(maxsize=1)
def build_local_retriever(k: int = 4, threshold: float = 0.4) -> BaseRetriever:
    """ builds the in-memory vector store and cretes the retriever for it

        cached so that each chain doesn't have to spend time and money re-creating the embeddings 
    """

    chunks = load_runbook_chunks()

    embeddings = BedrockEmbeddings(
        model_id=config.EMBED_MODEL_ID,
        region_name=config.AWS_REGION
    )

    store = InMemoryVectorStore.from_documents(chunks, embeddings)

    return ScoreThresholdRetriever(store=store, k=k, threshold=threshold)


def build_kb_retriever(k: int = 4, threshold: float = 0.4) -> BaseRetriever:
    """ Grab a knowledge base from Amazon Bedrock and create the retriever for it """

    return AmazonKnowledgeBasesRetriever(
        knowledge_base_id=config.BEDROCK_KB_ID,
        region_name=config.AWS_REGION,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": k}},
        min_score_confidence=threshold
    )

def get_retriever(k: int = 4) -> BaseRetriever:
    if config.BEDROCK_KB_ID:
        return build_kb_retriever(k=k)
    return build_local_retriever(k=k)


if __name__ == "__main__":

    retriever = get_retriever()

    QUERIES = [
        "What is a SEV3 used for?",
        "Is it safe to roll back a deployment for the checkout-api?",
        "The payments queue is backing up. What should we do?"
    ]

    for q in QUERIES:
        for doc in retriever.invoke(q):
            print(doc.metadata)
        print()