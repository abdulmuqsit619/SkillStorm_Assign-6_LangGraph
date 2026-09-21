""" Factory to create multiple different types of worker agents (graphs) """


import operator
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from oncall.llm import get_chat_model
from oncall.prompts import SPECIALIST_TEMPLATE
from oncall.tools.tools import CHANGE_TOOLS, HEALTH_TOOLS


MAX_SPECIALIST_TOOL_ROUNDS = 3


class SpecialistState(TypedDict):
    """A worker's private state. Deliberately tiny so each agent only has access to what it needs. Nothing more. """

    task: str
    messages: Annotated[list[AnyMessage], add_messages]
    findings: Annotated[list[str], operator.add]
    rounds: int


def build_specialist(name: str, brief: str, tools: list[BaseTool]):
    """ each specialist is just its own graph. this is a factory function that can build multiple types of specialists """

    system = SPECIALIST_TEMPLATE.format(name=name, brief=brief)
    model = get_chat_model().bind_tools(tools)

    # node for prompting the model
    def agent(state: SpecialistState) -> dict:
        history = list(state.get("messages") or [])
        seed: list = []
        if not history:
            seed = [SystemMessage(system), HumanMessage(state["task"])]
            history = seed

        reply = model.invoke(history)
        update: dict = {
            "messages": seed + [reply],
            "rounds": state.get("rounds", 0) + 1,
        }
        if not reply.tool_calls and reply.text.strip():
            update["findings"] = [f"{name}: {reply.text}"]
        return update

    # tool node
    def run_tools(state: SpecialistState, config) -> dict:
        return ToolNode(tools).invoke(state, config)

    # route after tools
    def route(state: SpecialistState) -> str:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            if state.get("rounds", 0) >= MAX_SPECIALIST_TOOL_ROUNDS:
                return END
            return "tools"
        return END

    # putting the graph together
    g = StateGraph(SpecialistState)
    g.add_node("agent", agent)
    g.add_node("tools", run_tools)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")

    # creating the agent sub-graph and naming it for tracing in LangSmith
    return g.compile(name=name)


SPECIALIST_BRIEFS = {
    "health_specialist": (
        "the service's CURRENT state. Error rates, healthy-versus-desired task "
        "counts, queue depth, disk usage, replica lag. You establish what is "
        "happening right now and how bad it is. You cannot see deployments."
    ),
    "change_specialist": (
        "recent changes. You establish whether a deployment could explain the "
        "alert. A deploy that finished shortly before an alert fired is the "
        "most common cause of a sudden change. Report the deploy id, when it "
        "finished, and whether it carried a migration. You cannot see live "
        "health metrics."
    ),
}

_TOOLSETS = {
    "health_specialist": HEALTH_TOOLS,
    "change_specialist": CHANGE_TOOLS,
}

# Lazily loading the specialists so that just importing the model doesn't create them - they should only be created when they're needed
_SPECIALISTS: dict | None = None

def get_specialists() -> dict:
    """Return the compiled specialists, building them once."""
    global _SPECIALISTS
    if _SPECIALISTS is None:
        _SPECIALISTS = {
            name: build_specialist(name, brief, _TOOLSETS[name])
            for name, brief in SPECIALIST_BRIEFS.items()
        }
    return _SPECIALISTS