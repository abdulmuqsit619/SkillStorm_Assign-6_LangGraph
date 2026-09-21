""" Nodes for the supervidor and worker sub-graphs """


from langchain_core.messages import HumanMessage, SystemMessage
from typing import cast

from oncall.llm import get_chat_model
from oncall.prompts import SUPERVISOR_PROMPT
from oncall.schemas import Delegation
from oncall.graph.specialists import get_specialists
from oncall.graph.state import IncidentState

# The supervisor may delegate at most this many times before it must finish.
MAX_DELEGATIONS = 3


def supervisor_node(state: IncidentState) -> dict:
    """Choose the next specialist, or declare the investigation finished.

    The supervisor has **no tools**. It cannot look anything up. 
    A Supervisor who can do work on their own will do work on their own and we don't want that.
    """
    already_used = [f.split(":")[0] for f in state.get("findings", [])]
    reports = "\n".join(state.get("findings", [])) or "(nothing yet)"
    triage = state.get("triage")

    ask = f"Alert:\n{state['alert']}\n"
    if triage:
        ask += f"\nTriage: {triage.severity} on {triage.service}\n"

    ask += (
        f"\nSpecialists already used: {already_used or 'none'}\n"
        f"Reports so far:\n{reports}\n\n"
        "Who works next?"
    )

    decision: Delegation = cast(
        "Delegation",
        get_chat_model()
        .with_structured_output(Delegation)
        .invoke([
            SystemMessage(SUPERVISOR_PROMPT), 
            HumanMessage(ask)
        ])
    )

    update = {
        "delegation": decision,
        "evidence": [f"supervisor -> {decision.next_worker}: {decision.reason}"], 
    }

    # tracking how many times the supervisor says to delegate
    if decision.next_worker != "done":
        update["delegation_attempts"] = state["delegation_attempts"] + 1

    return update


def route_after_supervisor(state: IncidentState) -> str:
    """ Turn the supervisor's  choice into an edge. """

    delegation = state.get("delegation")
    if delegation is None or delegation.next_worker == "done":
        return "retrieve"

    # if the supervisor is delegating too many times, move on to retrieval
    if state["delegation_attempts"] >= MAX_DELEGATIONS:
        return "retrieve"

    # if a specialist has already ran, don't let it run again
    worker = delegation.next_worker
    if any(f.startswith(worker) for f in state.get("findings", [])):
        return "retrieve"

    return worker


def _run_specialist(name: str, state: IncidentState) -> dict:
    """ Invoke one specialist subgraph and map its result back. """

    triage = state.get("triage")
    task = f"Alert:\n{state['alert']}\n"

    if triage:
        task += f"Triage: {triage.severity} on {triage.service}.\n"
    task += "Investigate within your brief and report."

    result = get_specialists()[name].invoke(
        {"task": task, "messages": [], "findings": [], "rounds": 0}
    )

    findings = result.get("findings") or [f"{name}: no findings"]
    return {"findings": findings, "trace": [name]}


def health_specialist_node(state: IncidentState) -> dict:
    return _run_specialist("health_specialist", state)


def change_specialist_node(state: IncidentState) -> dict:
    return _run_specialist("change_specialist", state)
