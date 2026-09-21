from langchain_core.messages import HumanMessage, SystemMessage

from policy_assistant.graph.state import AssistantState
from policy_assistant.llm import get_chat_model
from policy_assistant.prompts import ANSWER_PROMPT
from policy_assistant.rag.retriever import retrieve_documents


MAX_RETRIEVAL_ATTEMPTS = 2


CONTEXT_PROMPT = """
Rewrite the latest user question as a standalone search query using the
conversation history.

Do not answer the question.

Return only the rewritten search query.
"""


REFRAME_PROMPT = """
A policy document search returned nothing useful.

Rewrite the user's question as ONE better search query.

Use short keywords likely to appear in company policy documents.

Do not answer the question.

Return only the search query.
"""


def contextualize_node(state: AssistantState) -> dict:
    """
    Turn a conversational question into a standalone retrieval query.

    Example:
        Previous: Does the Standard plan include SSO?
        Current: Is that the same for Enterprise?

    Could become:
        Does the Enterprise plan include SSO?
    """

    question = state["question"]
    messages = state.get("messages", [])

    # If there is no useful conversation history yet,
    # just search using the current question.
    if len(messages) <= 1:
        return {
            "search_query": question,
        }

    response = get_chat_model().invoke(
        [
            SystemMessage(content=CONTEXT_PROMPT),
            *messages,
        ]
    )

    query = str(response.content).strip()

    if not query:
        query = question

    return {
        "search_query": query,
    }


def retrieve_node(state: AssistantState) -> dict:
    """
    Retrieve policy documents using the current search query.
    """

    query = state.get("search_query") or state["question"]

    documents = retrieve_documents(query)

    attempts = state.get("retrieval_attempts", 0) + 1

    return {
        "documents": documents,
        "retrieval_attempts": attempts,
    }


def route_after_retrieval(state: AssistantState) -> str:
    """
    Decide what happens after retrieval.

    Good retrieval:
        -> answer

    Weak retrieval + retries remaining:
        -> reframe

    Weak retrieval + attempts exhausted:
        -> refuse
    """

    documents = state.get("documents", [])
    attempts = state.get("retrieval_attempts", 0)

    if documents:
        return "answer"

    if attempts < MAX_RETRIEVAL_ATTEMPTS:
        return "reframe"

    return "refuse"


def reframe_node(state: AssistantState) -> dict:
    """
    Rewrite a failed search query before trying retrieval again.
    """

    question = state["question"]

    failed_query = (
        state.get("search_query")
        or question
    )

    prompt = (
        f"Original question: {question}\n"
        f"Failed search query: {failed_query}\n\n"
        "Return a better search query."
    )

    response = get_chat_model().invoke(
        [
            SystemMessage(content=REFRAME_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    new_query = str(response.content).strip().strip('"')

    if not new_query:
        new_query = question

    return {
        "search_query": new_query,
    }


def format_documents(state: AssistantState) -> str:
    """
    Convert retrieved documents into text that can be sent to the LLM.
    """

    blocks: list[str] = []

    for document in state.get("documents", []):
        source = document.metadata.get(
            "source",
            "unknown",
        )

        blocks.append(
            f"--- Source: {source} ---\n"
            f"{document.page_content}"
        )

    return "\n\n".join(blocks)


def answer_node(state: AssistantState) -> dict:
    """
    Generate an answer using ONLY retrieved policy documents.
    """

    documents = state.get("documents", [])

    if not documents:
        return {
            "answer": "The provided documents do not cover that.",
        }

    context = format_documents(state)

    system_prompt = ANSWER_PROMPT.format(
        context=context
    )

    question = state["question"]

    response = get_chat_model().invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
    )

    sources = sorted(
        {
            str(
                document.metadata.get(
                    "source",
                    "unknown",
                )
            )
            for document in documents
        }
    )

    answer = str(response.content).strip()

    return {
        "answer": answer,
        "sources": sources,
    }


def refuse_node(state: AssistantState) -> dict:
    """
    Deterministically refuse unsupported questions.
    """

    return {
        "answer": "The provided documents do not cover that.",
    }