
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from oncall.llm import get_chat_model
from oncall.prompts import STATUS_PROMPT
from oncall.graph.state import IncidentState
from oncall.schemas import StatusUpdate


def execute_node(state: IncidentState) -> dict:
    """Carry out the approved action."""

    plan = state.get("plan")
    assert plan is not None, "execute reached without a plan"
    detail = f"{plan.action} on {plan.target}"        # type: ignore[union-attr]
    if plan.argument:
        detail += f" ({plan.argument})"
    return {
        "outcome": f"EXECUTED {detail}",
        "evidence": [f"executed {detail}"],
    }


def escalate_node(state: IncidentState) -> dict:
    """Hand off to a human, with everything we learned attached."""

    diagnosis = state.get("diagnosis")
    plan = state.get("plan")

    if state.get("approval") == "rejected":
        reason = "human rejected the proposed remediation"
    elif not (diagnosis and diagnosis.grounded):
        reason = "no runbook covers this alert"
    elif plan is None:
        reason = "could not form a plan"
    elif plan.action == "escalate_to_human":
        reason = f"runbook action needs a human: {plan.rationale}"
    else:
        reason = "unknown"

    return {
        "outcome": f"ESCALATED: {reason}",
        "evidence": [f"escalated: {reason}"],
    }


def write_status_node(state: IncidentState) -> dict:
    """Draft a customer-facing update -- but only when policy requires one."""

    triage = state.get("triage")
    diagnosis = state.get("diagnosis")
    severity = (diagnosis.severity if diagnosis and diagnosis.severity
                else triage.severity if triage else "SEV3")

    if severity not in ("SEV1", "SEV2"):
        return {
            "status_update": None,
            "evidence": [f"no status page update required for {severity}"],
        }

    draft = cast(
        "StatusUpdate",
        get_chat_model(temperature=0.3)
        .with_structured_output(StatusUpdate)
        .invoke([SystemMessage(STATUS_PROMPT), HumanMessage(state["alert"])])
    )

    return {
        "status_update": draft,
        "evidence": ["drafted status page update"],
    }


def close_node(state: IncidentState) -> dict:
    """Final node. Make sure every path ends with a stated outcome."""

    outcome = state.get("outcome") or "CLOSED with no action"
    return {"outcome": outcome}