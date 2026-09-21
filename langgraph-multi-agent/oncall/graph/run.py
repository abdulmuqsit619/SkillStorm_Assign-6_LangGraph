
from oncall.graph.graph import build_graph, build_graph_with_memory
from oncall.fixtures import ALERTS
from oncall.graph.state import IncidentState
import uuid

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command



def print_steps(app, graph_state, config: RunnableConfig):
    for chunk in app.stream(graph_state, config, stream_mode="updates"):
        print("=================================")
        print(chunk)

        if "__interrupt__" in chunk:
            return "interrupted"

        print()

    return "closed"



if __name__ == "__main__":

    app = build_graph_with_memory()

    alert_index = 0
    alert = ALERTS[alert_index]

    # creating a thread id for our graph state 
    thread_id = uuid.uuid4()
    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,

            # naming the run to appear in LangSmith
            "run_name": f"[{thread_id}] - Alert {alert_index + 1}"     
        }
    }

    state = {
        "alert": alert,
        "messages": [],
        "evidence": [],
        "trace": [],
        "retrieval_attempts": 0,
        "tool_attempts": 0,
        "delegation_attempts": 0
    }

    status: str = "new"
    while status != "closed":
        status = print_steps(app, state, config)

        # handle interruptions
        if status == "interrupted":
            answer = input("approve / reject > ") or "reject"
            state = Command(resume=answer)

    final_state = app.get_state(config).values
    for node in final_state.get("trace", []):
        print(f"{node} ->")