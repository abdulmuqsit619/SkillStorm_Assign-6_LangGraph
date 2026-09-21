# Runbook: orders-db high CPU and replica lag

Service: orders-db-prod (RDS PostgreSQL)
Owner: Data Platform
Alarm: `orders-db-cpu`
Last reviewed: 2026-06-30

## What this alarm means

CPU utilisation on the orders-db writer instance exceeded 90% for more than 5
minutes. orders-db backs checkout-api, order-history, and the finance export.

## Replica lag is the number that decides severity

CPU alone is not the impact. **Read replica lag is.** order-history reads from
the replica, so lag translates directly into customers seeing stale orders.

| Replica lag | Severity | Why |
|---|---|---|
| Under 10s | SEV3 | Within normal variance, customers do not notice |
| 10s to 60s | SEV2 | order-history shows stale data; customers notice |
| Over 60s | SEV2 | As above, and the finance export will miss its window |
| Any lag with writes failing | SEV1 | Checkout is affected — core journey |

**Writes still succeeding is the key qualifier.** If checkout-api is still
capturing orders, this is degradation and not an outage, regardless of how bad
the CPU graph looks.

## First checks

1. **Look for a long-running query.** `pg_stat_activity` ordered by
   `query_start`. A single unindexed analytical query is the most common cause.
2. **Check for a recent migration.** Migrations that add an index without
   `CONCURRENTLY` take an exclusive lock and will present as CPU saturation
   plus climbing lag.
3. **Check connection count against `max_connections`.** checkout-api holds 20
   connections per task; a scale-out event can exhaust the limit.

## Mitigations

- **Kill the offending query** — safe, reversible, and usually sufficient.
- **Fail over to the replica** — requires Data Platform approval. Promotion is
  irreversible and drops any transaction not yet replicated.
- **Scale the instance class** — takes 10 to 20 minutes and causes a restart.
  Not a mitigation during an active incident.

## Do not

Do not restart orders-db to clear CPU. A restart during high write volume
extends recovery by the length of crash recovery, typically 4 to 12 minutes,
and turns a SEV2 into a SEV1.
