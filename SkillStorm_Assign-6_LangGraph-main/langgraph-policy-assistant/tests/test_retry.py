from policy_assistant.graph.nodes import (
    MAX_RETRIEVAL_ATTEMPTS,
    route_after_retrieval,
)
from policy_assistant.graph.state import AssistantState


def test_retry_bound_routes_to_refuse():
    state: AssistantState = {
        "question": "Do you offer student discounts?",
        "messages": [],
        "documents": [],
        "retrieval_attempts": MAX_RETRIEVAL_ATTEMPTS,
        "sources": [],
    }

    result = route_after_retrieval(state)

    assert result == "refuse"