
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.memory import InMemorySaver

from oncall.schemas import Triage, Diagnosis, RemediationPlan, StatusUpdate, Delegation
from oncall.graph.state import IncidentState
from oncall.graph.nodes.investigation import triage_node
from oncall.graph.nodes.diagnosis import diagnose_node, reframe_node, retrieve_node, route_after_diagnose
from oncall.graph.nodes.remediation import human_approval_node, plan_remediation_node, route_after_approval, route_after_plan
from oncall.graph.nodes.resolution import close_node, escalate_node, execute_node, write_status_node
from oncall.graph.nodes.supervision import supervisor_node, health_specialist_node, change_specialist_node, route_after_supervisor


# using the serializer to convert pydantic models to and from JSON
SERDE = JsonPlusSerializer(allowed_msgpack_modules=[Triage, Diagnosis, RemediationPlan, StatusUpdate, Delegation])

# checkpointer will write graph state into memory
#   InMemorySaver - saves state into app memory
#   PostgresSaver - saves state into a Postgres database
#       https://docs.langchain.com/oss/python/langgraph/persistence
#       https://pypi.org/project/langgraph-checkpoint-postgres/
#       https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-postgres
def build_graph(checkpointer=None):

    graph = StateGraph(IncidentState)

    # --- NODES ---
    graph.add_node("triage", triage_node)

    # investigation is now handled by the agents, so no more investigation and tool nodes or edges
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("health_specialist", health_specialist_node)
    graph.add_node("change_specialist", change_specialist_node)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("diagnose", diagnose_node)
    graph.add_node("reframe", reframe_node)

    graph.add_node("plan_remediation", plan_remediation_node)
    graph.add_node("human_approval", human_approval_node)
    
    graph.add_node("escalate", escalate_node)
    graph.add_node("execute", execute_node)
    graph.add_node("write_status", write_status_node)
    graph.add_node("close", close_node)


    # --- EDGES ---
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "supervisor")

    # SUPERVISOR AND WORKER EDGES
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "health_specialist": "health_specialist",
            "change_specialist": "change_specialist",
            "retrieve": "retrieve",
        },
    )
    graph.add_edge("health_specialist", "supervisor")
    graph.add_edge("change_specialist", "supervisor")

    graph.add_edge("retrieve", "diagnose")

    graph.add_conditional_edges(
        "diagnose",
        route_after_diagnose,
        {
            "plan_remediation": "plan_remediation",
            "reframe": "reframe",
            "escalate": "escalate"
        }
    )

    graph.add_edge("reframe", "retrieve")

    graph.add_conditional_edges(
        "plan_remediation",
        route_after_plan,
        {
            "human_approval": "human_approval",
            "escalate": "escalate",
            "execute": "execute",
            "write_status": "write_status"
        }
    )

    graph.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "escalate": "escalate",
            "execute": "execute"
        }
    )

    graph.add_edge("execute", "write_status")
    graph.add_edge("escalate", "write_status")
    graph.add_edge("write_status", "close")
    graph.add_edge("close", END)

    return graph.compile(checkpointer=checkpointer)

def build_graph_with_memory():
    """ builds the graph with a checkpointer so the state can survive an interruption """
    return build_graph(checkpointer=InMemorySaver(serde=SERDE))


if __name__ == "__main__":
    app = build_graph()
    print(app.get_graph().draw_mermaid())