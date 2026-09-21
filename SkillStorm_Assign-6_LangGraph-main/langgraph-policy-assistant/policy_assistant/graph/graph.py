from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from policy_assistant.graph.nodes import (
    answer_node,
    contextualize_node,
    reframe_node,
    refuse_node,
    retrieve_node,
    route_after_retrieval,
)
from policy_assistant.graph.state import AssistantState


def build_graph(checkpointer=None):
    builder = StateGraph(AssistantState)

    
    # Nodes
    
    builder.add_node(
        "contextualize",
        contextualize_node,
    )

    builder.add_node(
        "retrieve",
        retrieve_node,
    )

    builder.add_node(
        "reframe",
        reframe_node,
    )

    builder.add_node(
        "answer",
        answer_node,
    )

    builder.add_node(
        "refuse",
        refuse_node,
    )

    
    # Edges
    
    builder.add_edge(
        START,
        "contextualize",
    )

    builder.add_edge(
        "contextualize",
        "retrieve",
    )

    builder.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "answer": "answer",
            "reframe": "reframe",
            "refuse": "refuse",
        },
    )

    # Required retry cycle.
    builder.add_edge(
        "reframe",
        "retrieve",
    )

    builder.add_edge(
        "answer",
        END,
    )

    builder.add_edge(
        "refuse",
        END,
    )

    return builder.compile(
        checkpointer=checkpointer
    )


def build_graph_with_memory():
    memory = InMemorySaver()

    return build_graph(
        checkpointer=memory
    )