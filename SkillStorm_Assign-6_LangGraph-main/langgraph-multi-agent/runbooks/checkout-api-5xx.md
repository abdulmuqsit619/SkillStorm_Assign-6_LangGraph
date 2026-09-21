# Runbook: checkout-api elevated 5xx

Service: checkout-api
Owner: Payments Platform
Alarm: `checkout-api-5xx-rate`
Last reviewed: 2026-08-02

## What this alarm means

The proportion of 5xx responses from checkout-api exceeded 1% over a 5-minute
window. checkout-api is a **core customer journey** under the severity policy,
so sustained 5xx here is never below SEV2.

## First checks, in order

1. **Look for a deployment inside the last 30 minutes.** Roughly seven out of
   ten checkout-api 5xx incidents in the last two years followed a deploy.
   Check the deploy log before anything else.
2. **Check healthy task count against desired count.** A gap means tasks are
   failing their health check and being replaced in a loop. See "crash loop"
   below.
3. **Check the orders-db connection pool.** checkout-api holds a pool of 20
   connections per task. If orders-db is saturated, checkout-api returns 503
   rather than 500 — the distinction tells you which service is at fault.

## Crash loop

If healthy tasks are below desired tasks and the number is not recovering, the
new task revision is failing its container health check. The deployment
circuit breaker will roll back automatically after **10 consecutive failed
task starts**, which takes roughly 8 minutes.

**Do not wait for the circuit breaker if the service is a core journey.**
Trigger the rollback manually — see below.

## Rollback

Rolling back checkout-api requires **a second engineer's approval** because
checkout-api writes to the payments ledger and a rollback across a schema
change can double-charge. Confirm with the deploy author or the Payments
Platform on-call before proceeding.

Rollback is safe without approval only when the previous revision is less than
24 hours old and no migration ran between the two revisions.

## Known false positive

A 5xx spike lasting **under 90 seconds** immediately following a scale-in event
is expected behaviour and is not an incident. Connections held by a terminating
task are dropped rather than drained. Fix is tracked in PLAT-2291.
