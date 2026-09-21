from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from oncall.graph.state import IncidentState
from oncall.prompts import PLAN_PROMPT
from oncall.llm import get_chat_model
from oncall.schemas import RemediationPlan


def plan_remediation_node(state: IncidentState) -> dict:
    """Turn the diagnosis into a concrete, typed action."""

    diagnosis = state.get("diagnosis")
    convo = list(state["messages"]) + [
        HumanMessage(
            "Runbook-grounded recommendation:\n"
            f"{diagnosis.recommended_action if diagnosis else 'none'}\n\n"
            "Now choose the single next action."
        )
    ]
    plan = cast(
        "RemediationPlan",
        get_chat_model()
        .with_structured_output(RemediationPlan)
        .invoke([SystemMessage(PLAN_PROMPT)] + convo)
    )
    return {
        "plan": plan,
        "evidence": [f"plan: {plan.action} on {plan.target}"], 
    }


def route_after_plan(state: IncidentState) -> str:
    """Destructive work needs a human. Everything else proceeds."""

    plan = state.get("plan")
    if plan is None:
        return "escalate"
    if plan.action == "escalate_to_human":
        return "escalate"
    if plan.action == "acknowledge_only":
        return "write_status"
    if plan.is_destructive:
        return "human_approval"
    return "execute"


def human_approval_node(state: IncidentState) -> dict:
    """Stop the graph and wait for a person."""

    plan = state.get("plan")
    assert plan is not None, "human_approval reached without a plan"
    diagnosis = state.get("diagnosis")

    decision = interrupt(
        {
            "question": "Approve this remediation?",
            "action": plan.action,
            "target": plan.target,
            "argument": plan.argument,
            "rationale": plan.rationale,
            "severity": diagnosis.severity if diagnosis else None,
            "sources": diagnosis.sources if diagnosis else [],
            "reply_with": ["approve", "reject"],
        }
    )

    verdict = str(decision).strip().lower()
    approved = verdict == "approve"
    return {
        "approval": "approved" if approved else "rejected",
        "approval_note": str(decision),
        "evidence": [f"human {'approved' if approved else 'REJECTED'} {plan.action}"],
    }


def route_after_approval(state: IncidentState) -> str:
    return "execute" if state.get("approval") == "approved" else "escalate"
