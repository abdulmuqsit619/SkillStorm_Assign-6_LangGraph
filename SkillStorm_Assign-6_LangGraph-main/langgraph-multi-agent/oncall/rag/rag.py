""" Using retrievers as a part of a chain for RAG """

from operator import itemgetter
from typing import cast, Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnableParallel

from ..chains import build_triage_chain
from ..llm import get_chat_model
from .retriever import get_retriever, load_runbook_chunks
from ..schemas import Triage, Diagnosis
from ..prompts import DIAGNOSIS_PROMPT


def format_query(triage: Triage) -> str:
    """ Removing unnecessary details so we can retrieve documents relevant to the alert
        rather than based on information the model came up with
    """
    return f"{triage.service} - {triage.summary}"

def format_docs(docs: list[Document]) -> str:
    """ turn each found doc into one long string that can be added to the model system prompt """

    blocks = []
    for doc in docs:
        meta = doc.metadata
        header = f"source: {meta.get("source", "unknown")}"
        if meta.get("section"):
            header += f" | section: {meta.get("section")}"

        blocks.append(f"--- {header} ---\n{doc.page_content.strip()}")

    result = "\n\n".join(blocks)
    return result

def enforce_grounding(diagnosis: Diagnosis) -> Diagnosis:
    """ Make sure the model actually grounded itself in the content, rather than just saying it did """

    known = {chunk.metadata["source"] for chunk in load_runbook_chunks()}
    valid_citations = [source for source in diagnosis.sources if source in known]

    # restructure the Diagnosis object if there were no valid sources
    if not valid_citations:
        return diagnosis.model_copy(
            update={
                "grounded": False, 
                "sources": [],
                "severity": None,
                "recommended_action": (
                    "Escalate to human. No sources found to answer question. "
                    f"Model returned with this action plan: {diagnosis.recommended_action}"
                )
            }
        )
    return diagnosis.model_copy(update={"sources": valid_citations})

def build_rag_chain(k: int = 4) -> Runnable:
    retriever = get_retriever(k=k)

    prompt = ChatPromptTemplate.from_messages([
        ("system", DIAGNOSIS_PROMPT),
        ("human", "{question}")
    ])

    structured_model: Runnable[Any, Diagnosis] = cast(
        "Runnable[Any, Diagnosis]", 
        get_chat_model().with_structured_output(Diagnosis)
    )

    return (RunnableParallel(
        question=itemgetter("question"),
        context=itemgetter("question") | retriever | RunnableLambda(format_docs)
    ) | prompt | structured_model | RunnableLambda(enforce_grounding))


def build_diagnosis_chain() -> Runnable:
    """ Putting the RAG chain together with our Triage chain to use RAG with the alert """

    rag = build_rag_chain()

    return RunnableParallel(triage=build_triage_chain()) | RunnableParallel(
        triage=itemgetter("triage"),
        diagnosis=(
            itemgetter("triage") | 
            RunnableLambda(format_query) | 
            RunnableLambda(lambda q: {"question" : q}) |
            rag
        )
    )


if __name__ == "__main__":
    from ..fixtures import ALERTS

    print("=== TRYING RAG CHAIN ===")
    chain = build_rag_chain()
    print(chain.invoke({"question": "The payments queue is backing up. What should we do?"}))

    print()
    print("=== FULL DIAGNOSIS CHAIN ===")
    diagnosis_chain = build_diagnosis_chain()
    print(diagnosis_chain.invoke({"alert": ALERTS[0]}))