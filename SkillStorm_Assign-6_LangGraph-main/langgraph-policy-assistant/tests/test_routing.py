from langchain_core.documents import Document

from policy_assistant.graph.nodes import (
    route_after_retrieval,
)
from policy_assistant.graph.state import AssistantState


def test_good_retrieval_routes_to_answer():
    state: AssistantState = {
        "question": "What is the refund policy?",
        "messages": [],
        "documents": [
            Document(
                page_content=(
                    "Customers may return eligible "
                    "products within 30 days."
                ),
                metadata={
                    "source": "refund-policy.md"
                },
            )
        ],
        "retrieval_attempts": 1,
        "sources": [],
    }

    result = route_after_retrieval(state)

    assert result == "answer"


def test_weak_retrieval_routes_to_reframe():
    state: AssistantState = {
        "question": "Do you offer student discounts?",
        "messages": [],
        "documents": [],
        "retrieval_attempts": 1,
        "sources": [],
    }

    result = route_after_retrieval(state)

    assert result == "reframe"


def test_exhausted_retrieval_routes_to_refuse():
    state: AssistantState = {
        "question": "Do you offer student discounts?",
        "messages": [],
        "documents": [],
        "retrieval_attempts": 2,
        "sources": [],
    }

    result = route_after_retrieval(state)

    assert result == "refuse"