""" a fixed set of alerts to develop against """

ALERTS: list[str] = [
    (
        "ALARM checkout-api-5xx-rate in ALARM at 14:02 UTC. "
        "5xx ratio moved 0.2% -> 96.4% over 3 minutes across all availability zones. "
        "Deployment d-8814 completed at 13:59 UTC. Synthetic checkout canary failing."
    ),
    (
        "ALARM nightly-reconciliation-duration in ALARM. "
        "Job finished in 51m against a p50 of 12m. Job completed successfully. "
        "Downstream finance export was not delayed."
    ),
    (
        "ALARM orders-db-cpu in ALARM. "
        "RDS instance orders-db-prod at 98% CPU for 11 minutes. "
        "Read replica lag 40s and climbing. Writes are still succeeding."
    ),
    (
        "ALARM sso-saml-callback-errors in ALARM. "
        "8.1% of SAML logins returning 400 since 09:12 UTC. "
        "Affects one identity provider only; password login unaffected."
    ),
    (
        "ALARM payments-worker-queue-depth in ALARM. "
        "Queue depth 41,200 and rising, consumer lag 22 minutes. "
        "No consumer errors logged. Payments are queued, not dropped."
    ),
    (
        "ALARM web-03-disk-used in ALARM. "
        "Log volume at 91% on a single instance in an auto-scaling group of 12. "
        "Log rotation is scheduled hourly; last rotation 40 minutes ago."
    ),
]