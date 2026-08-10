# Decisions (ADRs)

Short Architecture Decision Records for changes that are expensive to reverse later.

## When an ADR is required

Write one before (or in the same change as) altering:

- layer direction (what `core/`/`common/`/`modules/*` are allowed to depend on),
- the transport strategy (versioning scheme, adding a second bot platform, switching auth's
  token strategy),
- the messaging topology (migrating from RabbitMQ to Kafka, splitting into a second deployable
  service),
- the public path-alias scheme.

Small, easily-reversible changes don't need one — if you're unsure, a short ADR is cheap;
a missing one for a real architectural pivot is expensive to reconstruct later.

## Format

One file per decision: `NNNN-short-title.md` (zero-padded sequential number). Keep it
short:

```md
# 0001: Short title

Date: 2026-07-25
Status: Accepted

## Context

What forced this decision.

## Decision

What was decided.

## Consequences

What this makes easier, harder, or forecloses.
```

## Review Checklist

- [ ] A layer/transport/messaging/alias-scheme change has a matching ADR in the same change.
- [ ] ADR file follows the `NNNN-short-title.md` naming and the format above.
