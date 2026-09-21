""" Nodes for phase 1 of the graph: investigate and find out what the problem is """

from oncall.chains import build_triage_chain
from oncall.graph.state import IncidentState
from oncall.rag.rag import format_query
from oncall.prompts import INVESTIGATE_PROMPT
from oncall.llm import get_chat_model
from oncall.tools.tools import ALL_TOOLS

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode


def triage_node(state: IncidentState) -> dict:
    triage = build_triage_chain().invoke({"alert": state["alert"]})

    return {
        "triage": triage,
        "search_query": format_query(triage),
        "evidence": [f"triage: {triage.severity} on {triage.service}"],
    }


def investigate_node(state: IncidentState) -> dict:
    """ letting the model decide which tools to call, and how many times """

    history = list(state.get("messages") or [])

    prompt_seed: list = []
    if not history:
        prompt_seed = [
            SystemMessage(INVESTIGATE_PROMPT), 
            HumanMessage(f"Alert: \n{state["alert"]}")
        ]
        history = prompt_seed

    model = get_chat_model().bind_tools(ALL_TOOLS)
    reply = model.invoke(history)

    partial_update = {
        "messages": prompt_seed + [reply],
    }

    # if the model is trying to do a tool call, then it didn't find anything new to add as evidence
    if not reply.tool_calls and reply.text.strip():
        partial_update["evidence"] = [f"investigation: {reply.text.strip()}"]

    return partial_update



def tools_node(state: IncidentState, config) -> dict:

    # wrapping aound LangGraph's built in tool node to add our own functionality: tool_attempts and evidence

    # ToolNode will read "tool_calls" property on the response, execute those tools, map the tool ids, 
    # and append a ToolMessage to the output
    output = ToolNode(ALL_TOOLS).invoke(state, config)
    executed_tools = [getattr(msg, "name", "?") for msg in output.get("messages", [])]

    return {
        **output, 
        "tool_attempts": state["tool_attempts"] + 1,
        "evidence": [f"ran tool {t}" for t in executed_tools],
    }


def route_after_investigation(state: IncidentState) -> str:

    last_message = state["messages"][-1]
    tool_rounds = state["tool_attempts"]

    # set the "budget" of how many tool rounds we will allow
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        if tool_rounds >= 5:
            return "retrieve"
        return "tools"
    return "retrieve"
