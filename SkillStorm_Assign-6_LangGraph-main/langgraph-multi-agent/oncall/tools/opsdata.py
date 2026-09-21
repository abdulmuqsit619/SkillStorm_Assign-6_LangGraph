""" create a fake backend that simulates available services in AWS """


# format this list of available services as if it was being returned from an API call
_SERVICES: dict[str, dict] = {
    "checkout-api": {
        "health": {
            "error_rate_pct": 96.4,
            "healthy_tasks": 2,
            "desired_tasks": 12,
            "p99_latency_ms": 8000,
            "status": "DEGRADED"
        },
        "deploys": [
            {
                "deploy_id": "d-8814",
                "finished_at": "2026-09-13T13:59:00Z",
                "minutes_ago": 7, 
                "author": "a.reeves",
                "summary": "Add idempotency key to capture endpoint",
                "includes_migration": True
            },
            {
                "deploy_id": "d-8802",
                "finished_at": "2026-09-11T09:12:00Z",
                "minutes_ago": 3047,
                "author": "r.banerjee",
                "summary": "Bump payment SDK to 4.2.1",
                "includes_migration": False,
            },
        ]
    },
    "orders-db-prod": {
        "health": {
            "cpu_pct": 98.0,
            "replica_lag_seconds": 40,
            "connections": 412,
            "max_connections": 500,
            "writes_succeeding": True,
            "status": "DEGRADED",
        },
        "deploys": [],
    },
    "payments-worker": {
        "health": {
            "queue_depth": 41200,
            "consumer_lag_minutes": 22,
            "consumer_error_rate_pct": 0.0,
            "healthy_tasks": 8,
            "desired_tasks": 8,
            "status": "HEALTHY",
        },
        "deploys": [],
    },
    "auth-gateway": {
        "health": {
            "saml_error_rate_pct": 8.1,
            "affected_idp_count": 1,
            "password_login_status": "HEALTHY",
            "healthy_tasks": 6,
            "desired_tasks": 6,
            "status": "DEGRADED",
        },
        "deploys": [],
    },
    "web-03": {
        "health": {
            "disk_used_pct": 91.0,
            "asg_name": "web-prod",
            "asg_size": 12,
            "asg_instances_alarming": 1,
            "minutes_since_log_rotation": 40,
            "status": "WARNING",
        },
        "deploys": [],
    },
    "nightly-reconciliation": {
        "health": {
            "last_run_minutes": 51,
            "p50_run_minutes": 12,
            "last_run_result": "SUCCESS",
            "status": "HEALTHY",
        },
        "deploys": [],
    },
}

# reference list of common terminology and the service above that it corresponds to
_ALIASES: dict[str, str] = {
    "sso-saml-callback-errors": "auth-gateway",
    "sso": "auth-gateway",
    "auth": "auth-gateway",
    "checkout": "checkout-api",
    "checkout-api-5xx-rate": "checkout-api",
    "orders-db": "orders-db-prod",
    "orders": "orders-db-prod",
    "payments-worker-queue": "payments-worker",
    "payments": "payments-worker",
    "web-03-disk-used": "web-03",
    "nightly-reconciliation-duration": "nightly-reconciliation",
}


def known_services() -> list[str]:
    return sorted(_SERVICES)

def health_of(service: str) -> dict | None:
    name = resolve_service_name(service)
    return dict(_SERVICES[name]["health"]) if name else None

def recent_deploys_of(service: str, minutes: int) -> list[dict] | None:
    name = resolve_service_name(service)

    if name is None:
        return None
    return [deploy for deploy in _SERVICES[name]["deploys"] if deploy["minutes_ago"] <= minutes]

def resolve_service_name(service: str) -> str | None:
    key = service.strip().lower()

    if key in _SERVICES:
        return key

    if key in _ALIASES:
        return _ALIASES[key]

    return None