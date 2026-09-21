# Runbook: payments-worker queue backlog

Service: payments-worker
Owner: Payments Platform
Alarm: `payments-worker-queue-depth`
Last reviewed: 2026-08-19

## What this alarm means

The payments-worker input queue exceeded 25,000 messages. The worker settles
authorised payments against the ledger; it does **not** sit in the checkout
path, so a backlog does not stop customers from completing a purchase.

## The promised processing window

The payments queue has a **30-minute processing guarantee**. Under the
severity policy, a backlog is not customer-facing until the oldest message in
the queue exceeds that window.

**So the number that matters is consumer lag, not queue depth.** A depth of
100,000 with a lag of 4 minutes is healthy throughput under load. A depth of
5,000 with a lag of 45 minutes is a breach.

| Consumer lag | Severity |
|---|---|
| Under 30 minutes | SEV3 |
| 30 to 60 minutes | SEV2 |
| Over 60 minutes, or any message loss | SEV1 |

## First checks

1. **Consumer error rate.** No errors with a growing queue means throughput,
   not failure — the workers are healthy and simply outnumbered.
2. **Worker task count.** payments-worker scales on queue depth with a
   3-minute cooldown; a sudden spike outruns the scaler for one or two cycles.
3. **Downstream ledger latency.** The worker is frequently blocked rather than
   broken. Ledger p99 above 2 seconds will back the queue up on its own.

## Mitigations

- **Raise the worker ceiling** — safe, and the default response. The ceiling
  exists to cap ledger write pressure, not to protect the worker.
- **Drain to the secondary queue** — requires Payments Platform approval.
  Messages moved to the secondary queue lose ordering, and ordering matters
  for refunds against the same authorisation.

## Never

**Never purge the payments queue.** Messages are authorisations that have
already been taken from the customer. Purging them means money is captured and
never settled, which is a financial-control incident and not an engineering
one.
