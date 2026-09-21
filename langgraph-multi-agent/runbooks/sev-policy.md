# Severity and Paging Policy

Owner: SRE Practice
Last reviewed: 2026-07-14

## Severity definitions

**SEV1** — Revenue-affecting or data-affecting. A core customer journey is
completely unavailable, or data is being lost or corrupted. Checkout,
authentication, and payment capture are the three journeys that qualify as
core.

**SEV2** — A core journey is degraded but completing for most users, or a
non-core journey is completely unavailable. Sustained error rates above 5% on
a customer-facing endpoint are SEV2 at minimum.

**SEV3** — Internal-only impact, or customer impact that is not yet occurring
but will if unattended. Capacity warnings, backlog growth with headroom
remaining, and failed internal jobs are SEV3.

**SEV4** — Informational. No action required outside business hours.

## Paging rules

Paging is decided by severity **and** time of day. Do not page on severity
alone.

| Severity | Business hours | Outside business hours |
|---|---|---|
| SEV1 | Page immediately | Page immediately |
| SEV2 | Page immediately | Page immediately |
| SEV3 | Ticket, no page | Ticket, no page |
| SEV4 | Ticket, no page | Ticket, no page |

Business hours are 08:00–18:00 in the on-call engineer's local time zone,
Monday to Friday, excluding company holidays.

## The 15-minute rule

**Any alert that is still unacknowledged 15 minutes after firing escalates one
severity level**, to a maximum of SEV1. An unacknowledged SEV3 becomes a SEV2
and therefore becomes pageable. This is the most commonly forgotten rule in
this document.

## Customer-facing determination

An incident is customer-facing if a person outside the company would notice it
without being told. Internal dashboards, batch jobs, and staff tooling are not
customer-facing regardless of how important they are internally.

**A queued backlog is not customer-facing until the queue's oldest item
exceeds the promised processing window for that queue.** Growth alone does not
make it customer-facing.

## Status page policy

A public status-page update is **required** for any SEV1 and for any SEV2 that
has lasted more than 20 minutes. Updates must not name internal services,
hosts, queues, databases, or deployment identifiers, and must not state a
cause before the incident review has concluded.
