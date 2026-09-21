# Runbook: instance disk pressure

Scope: any EC2 instance in a web or worker auto-scaling group
Owner: Platform
Alarm: `*-disk-used`
Last reviewed: 2026-04-22

## What this alarm means

A monitored volume exceeded 85% used. This alarm fires per instance, not per
service, so it is noisy by design.

## Instance count is the first question

A single instance in a healthy auto-scaling group is **not an incident**. The
group will replace an unhealthy instance on its own, and traffic is already
distributed across the remaining members.

| Situation | Severity |
|---|---|
| One instance in a group of 3 or more | SEV4 — ticket, no page |
| More than one third of a group | SEV3 |
| All instances in a group, or a stateful volume | SEV2 |
| A database or ledger volume | SEV1 |

## Log volumes are usually self-correcting

Log volumes rotate hourly. **A log volume above 85% with a rotation due inside
the hour is expected and requires no action** — the alarm exists to catch
rotation having stopped, not to report normal high-water marks.

Check when the last rotation completed. If it is inside the last hour,
acknowledge the alert and move on.

## When it is real

Disk pressure is genuine when one of these is true:

1. **Rotation has stopped.** Last rotation more than 2 hours ago.
2. **A single file is growing without bound** — usually a debug log level left
   on after an incident. This is the second most common cause and it is
   self-inflicted.
3. **The volume is stateful** — a database, a queue spool, or an upload
   staging area. These do not self-correct and will fail writes at 100%.

## Mitigations

- **Force a log rotation** — safe, no approval needed.
- **Terminate the instance** and let the group replace it. Safe for stateless
  web and worker nodes; **never** for a stateful volume.
- **Expand the volume** — required for stateful volumes, needs Platform
  approval, and takes effect without a restart on modern volume types.
