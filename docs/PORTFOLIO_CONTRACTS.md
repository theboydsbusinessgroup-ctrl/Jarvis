# Portfolio Contracts

JARVIS coordinates the portfolio but does not become the source of truth for domain systems.

## Event contract
All systems may continue emitting the deployed v1.0 adapter shape:
`schema_version`, `event_id`, `project_id`, `event_type`, `occurred_at`, `payload`.

JARVIS normalizes accepted events to v1.1 by adding `source_system`, `received_at`, and `idempotency_key` when omitted. This keeps current adapters backward compatible while giving the control plane a stable canonical envelope.

## Health contract
Each system should expose or generate a `project-health/v1` snapshot. The contract separates:
- lifecycle stage
- technical health
- deployment state
- revenue state
- CI state
- funnel/revenue metrics
- blockers and next action
- whether Eric is actually required

## Operating rule
A repository's own database, API, marketplace, deployment platform, or provider remains authoritative. JARVIS stores observations and evidence; it must not infer a sale, deployment, approval, or customer event that was not verified from an authoritative source.
