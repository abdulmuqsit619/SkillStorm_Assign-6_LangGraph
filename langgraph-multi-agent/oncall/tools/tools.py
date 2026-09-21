""" defining the tools for langchain to use """

from langchain_core.tools import tool
from . import opsdata


# make sure to include docstring comment to tell the model what the tool is and how it works
# type hints will also be passed along to the model so it knows how to pass in data and the data it will receive back
@tool
def get_service_health(service: str) -> dict:
    """ 
        Get the current health snapshot for one service.

        Returns live operational metrics such as error rate, latency, replica lag, 
        queue depth, disk usage, and healthy-versus-desired task counts. Different 
        metrics will come back for different services.

        Use this whenever an alert names a service and you need to know its current state
        rather than guessing or assuming the alert's given state is still accurate.
    """

    health = opsdata.health_of(service)
    if health is None:
        return {
            "error": f"Unknown Service {service}",
            "known_services": opsdata.known_services()
        }
    return {
        "service": service,
        "health": health
    }


@tool
def get_recent_deploys(service: str, within_minutes: int = 120) -> dict:
    """ List deployments to a service that finished within the last N minutes.

        Use this when an alert names a service and you need to know whether a
        recent code change could explain it. A deployment that finished shortly
        before an alert fired is the single most common cause of a sudden change in
        error rate.

        An empty list is a meaningful answer: it means nothing was deployed in that
        window, so a deploy is not the explanation. Not every service is deployed
        at all -- managed databases and queues never are.
    """

    deploys = opsdata.recent_deploys_of(service, within_minutes)
    if deploys is None:
        return {
            "error": f"Unknown Service {service}",
            "known_services": opsdata.known_services()
        }
    return {
        "service": service,
        "within_minutes" : within_minutes,
        "deploys": deploys
    }


@tool
def list_known_services() -> list[str]:
    """ List every service name this system can look up.

        Use this when a service name from an alert is not recognized.
    """
    return opsdata.known_services()

# creating lists of all our tools to BIND to the model
ALL_TOOLS = [get_service_health, get_recent_deploys, list_known_services]
TOOL_REGISTRY = {t.name: t for t in ALL_TOOLS}

# SCOPING THE TOOLSETS TO THEIR RESPECTIVE AGENTS
HEALTH_TOOLS = [get_service_health, list_known_services]
CHANGE_TOOLS = [get_recent_deploys]