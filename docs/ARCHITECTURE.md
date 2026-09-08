# JARVIS Architecture

## 1. Purpose

JARVIS is a personal control plane for multiple autonomous income systems. Its job is to create one reliable view of money, system health, opportunities, risk, and authorized actions.

## 2. Logical layers

### Source systems
Independent engines execute their own domain workflows and retain their own source-of-truth data.

### Integration adapters
Adapters translate source-system health, financial events, opportunities, and permitted actions into a common JARVIS contract.

### Event normalization
All inbound events are converted into a canonical envelope with source, tenant, event type, occurred-at timestamp, idempotency key, payload, and evidence metadata.

### Intelligence
JARVIS derives contribution income, run rate, forecasts, health scores, anomalies, opportunity rankings, and recommended actions.

### Control plane
Permissions, policy, risk tier, approvals, idempotency, audit logging, and action verification govern execution.

### Command center
The dashboard presents a single operational picture without pretending that disconnected sources are live.

## 3. Authority model

- GREEN: autonomous low-risk observation, calculation, reporting, retries, classification, and analytics.
- YELLOW: approval normally required for material spend, pricing changes, campaigns, provider changes, publishing with reputational impact, or meaningful capital allocation.
- RED: human-only for large transfers, credential/account changes, destructive operations, legal commitments, and high-risk financial actions.

Authority is evaluated by deterministic policy before an action can execute.

## 4. Canonical financial model

`gross_revenue - processing_fees - marketplace_fees - fulfillment_cost - labor - advertising - software/infrastructure - other_known_expenses = contribution_income`

Unknown costs must be marked unknown. Estimates must carry an explicit confidence/status flag.

## 5. Canonical event model

Each event contains:

- `event_id`
- `event_type`
- `source_system`
- `source_event_id`
- `occurred_at`
- `received_at`
- `idempotency_key`
- `amount` and `currency` when financial
- `entity_type` / `entity_id`
- `confidence`
- `evidence`
- `payload`

## 6. System contract

Each adapter should eventually expose:

- `/system/status`
- `/system/health`
- `/system/revenue`
- `/system/expenses`
- `/system/profit`
- `/system/forecast`
- `/system/activity`
- `/system/opportunities`
- `/system/alerts`
- `/system/actions`

These are conceptual contracts first; adapters can map them to native APIs/events.

## 7. Resilience

- No cross-system transaction should depend on synchronous availability of another engine.
- Events are idempotent.
- Failed deliveries retry with bounded backoff.
- Dead-lettered events are visible in the JARVIS Inbox.
- Actions use idempotency keys and post-action verification.
- Read-only operation remains possible when an integration is degraded.

## 8. Trading boundary

JARVIS may aggregate trading status, performance, and risk information. It may later request an authorized trading action, but execution must flow through the Autonomous Trading System's deterministic risk and execution layers. JARVIS never has a direct broker-order path.
