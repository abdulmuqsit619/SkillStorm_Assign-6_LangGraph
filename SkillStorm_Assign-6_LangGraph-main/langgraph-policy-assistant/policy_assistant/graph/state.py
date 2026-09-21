import operator
from typing import Annotated, NotRequired, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AssistantState(TypedDict):
    """Complete state used internally by the LangGraph."""

    question: str

    # add_messages prevents new messg from overwriting old messg.
    messages: Annotated[list[AnyMessage], add_messages]

    #used for retrieval.
    search_query: NotRequired[str]

    # Docs returned by retrieval.
    documents: list[Document]

    # Number of retrieval attempts for the current question.
    retrieval_attempts: int

    # Final response.
    answer: NotRequired[str]

    # Sources accumulate rather than overwrite.
    sources: Annotated[list[str], operator.add]


class AssistantInput(TypedDict):
    """State supplied when a new user question enters the graph."""

    question: str
    messages: Annotated[list[AnyMessage], add_messages]
    documents: list[Document]
    retrieval_attempts: int
    sources: list[str]