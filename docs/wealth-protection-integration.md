# Wealth Management Protection Protocol — JARVIS Integration

## Purpose

Fold the Wealth Management Protection Protocol into JARVIS as a first-class module while preserving a strict security boundary between portfolio intelligence and protected customer data.

## Product identity

- Repository: `theboydsbusinessgroup-ctrl/Wealth-Management-Protection-protocol`
- Product concept: **Digital Estate Protection**
- JARVIS module label: **Wealth Protection**
- Business model: low-touch recurring revenue

## What the product does

Continuously monitors an affluent customer's digital estate and identifies meaningful exposure or risk signals, then provides clear alerts, recommendations, reporting, and authorized remediation workflows.

Monitoring domains include identity exposure, public/personal information exposure, email/breach signals, credential exposure signals, domains and impersonation risk, social/public exposure, family exposure, property/public-record exposure, reputation signals, and important documents/deadlines.

## JARVIS boundary

JARVIS receives portfolio telemetry and operational health, not a duplicate copy of the protected customer database.

### JARVIS may receive

- Aggregate business KPIs
- Monitoring health
- Alert counts by severity
- Human-review queue size
- Agent health
- Integration health
- Data freshness
- Cost and revenue telemetry
- Opaque customer identifiers when needed for routing
- Deep links to the protected application

### JARVIS must not receive by default

- Passwords
- Raw third-party credentials
- Payment-card information
- Secrets/API keys
- Full identity profiles
- Sensitive family records
- Raw breach records when a summary is sufficient
- Full customer monitoring evidence unless required for an authorized operational workflow

## Event contract

The module should publish normalized events for:

- `customer.subscription.changed`
- `customer.lifecycle.changed`
- `monitoring.run.completed`
- `monitoring.run.failed`
- `risk.alert.created`
- `risk.alert.resolved`
- `human_review.created`
- `human_review.resolved`
- `agent.execution.failed`
- `integration.health.changed`
- `billing.event.received`
- `cost.recorded`

Each event should include an event ID, source, timestamp, schema version, severity where relevant, correlation ID, and opaque entity reference.

## KPI contract

```json
{
  "mrr": null,
  "arr": null,
  "active_customers": null,
  "trial_customers": null,
  "churn_rate": null,
  "conversion_rate": null,
  "contribution_margin": null,
  "ai_cost": null,
  "api_cost": null,
  "infrastructure_cost": null,
  "support_cost": null,
  "critical_alerts": null,
  "high_alerts": null,
  "medium_alerts": null,
  "human_review_queue": null,
  "monitoring_health": "unknown",
  "integration_health": "unknown",
  "last_successful_monitoring_run": null,
  "data_freshness": null
}
```

`null` or `unknown` is intentional when a live source is not connected. JARVIS must never invent values.

## Agent boundary

The protected application owns monitoring, risk analysis, research, reporting, quality control, and customer-specific remediation agents. JARVIS may observe agent health and route approved operational tasks, but it should not bypass the protected application's authorization layer.

## Security requirements

- Least-privilege API credentials
- Signed/authenticated telemetry requests
- Tenant isolation in the protected application
- Audit logging
- Encryption in transit and at rest
- No secrets committed to source control
- Idempotent event processing
- Replay protection where applicable
- Rate limiting
- Explicit authorization for any write action
- Human approval for sensitive or irreversible actions

## Dashboard UX

The JARVIS Wealth Protection page should contain:

1. Revenue and margin summary
2. Customer count and lifecycle
3. Monitoring health
4. Alert distribution
5. Human-review queue
6. Agent/integration health
7. Cost-to-serve
8. Data freshness
9. Recent operational events
10. Link to the protected application

The page should answer whether this income engine is healthy and whether the operator needs to intervene without exposing unnecessary customer details.
