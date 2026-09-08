# JARVIS

## Personal Autonomous Income Command Center

JARVIS is the orchestration and intelligence layer above the user's independent income engines and operating systems. It does not replace those systems or bypass their safety controls. It observes, normalizes, measures, forecasts, prioritizes, alerts, and—only when authorized—coordinates actions through each system's own authority boundary.

### Core principle

**Observe → Understand → Verify → Decide → Act → Verify → Measure → Learn → Improve → Earn Authority**

### Integrated portfolio

- Boyd's Bar OS
- Productized AI Service
- Service Arbitrage
- Autonomous Product Discovery Engine
- Autonomous Trading System
- EventMatch
- **Wealth Management Protection Protocol / Digital Estate Protection**

### New Wealth Protection module

The Wealth Management Protection Protocol repository contains the protected product domain. JARVIS folds it into the command center as a first-class portfolio module.

The customer-facing product remains **Digital Estate Protection**. The repository/project name is not intended to imply investment management, financial advice, or custody of wealth.

JARVIS should surface:

- MRR / ARR
- Active and trial customers
- Conversion and churn
- Acquisition source
- Contribution margin
- AI, API, infrastructure, support, and other operating costs
- Monitoring health and data freshness
- Critical/high/medium alert counts
- Human-review queue
- Agent execution health
- Integration health
- Last successful monitoring run

JARVIS should link back to the protected application for customer-level detail rather than copying unnecessary sensitive personal data into the central dashboard.

### Architecture rules

1. Each source system remains independently deployable and owns its operational source of truth.
2. JARVIS stores normalized cross-system intelligence and financial/operational events, not duplicate operational databases.
3. Revenue is never treated as profit. JARVIS calculates contribution income after known fees, labor, fulfillment, advertising, infrastructure, marketplace costs, and other expenses.
4. AI recommendations are advisory until deterministic policy grants authority.
5. Trading actions must pass through the Autonomous Trading System's risk engine; JARVIS never sends orders directly to a broker.
6. Money movement, credential changes, destructive operations, protected-customer actions, and other RED actions remain human-controlled until explicitly connected and authorized.
7. Every decision and action is auditable.
8. Missing integrations are represented honestly as unavailable or estimated—not fabricated as real-time data.
9. Sensitive customer data is minimized, compartmentalized, encrypted, and accessed by least privilege.
10. JARVIS is the visibility/orchestration layer; domain repositories remain the source of truth.

## Dashboard architecture

### Command Center

The home view should answer, at a glance:

- How much money is being generated now?
- Which engines are growing or declining?
- What requires attention?
- What is automated successfully?
- What failed?
- What is the next highest-value action?
- Are any systems stale, disconnected, or unsafe?

### Income

Separate realized cash, booked revenue, expected revenue, recurring revenue, expenses, contribution income, and forecasts. Every value must have a source and freshness timestamp.

### Projects

Each project gets a health card containing stage, automation level, revenue, margin, active exceptions, next milestone, and blockers.

### Wealth Protection

Dedicated view for Digital Estate Protection with business KPIs, monitoring health, risk/alert distribution, agent status, customer counts, and operator exceptions. Customer-sensitive findings stay in the protected application.

### Automation

Centralized view of agent runs, scheduled jobs, failures, retries, queue depth, exception count, and estimated operator hours saved.

### Alerts

Cross-system exception feed ordered by severity, confidence, business impact, and required action. Routine noise should be suppressed/deduplicated.

### System Health

Integrations, API health, job freshness, billing webhooks, notifications, security events, deployments, backups, and data-source status.

## Wealth Protection integration contract

The protected product should eventually expose a machine-readable portfolio telemetry contract containing:

```text
mrr
arr
active_customers
trial_customers
churn_rate
conversion_rate
acquisition_source
contribution_margin
ai_cost
api_cost
infrastructure_cost
support_cost
monitoring_health
critical_alerts
high_alerts
medium_alerts
human_review_queue
last_successful_monitoring_run
integration_health
data_freshness
```

Customer-level data should use opaque IDs and deep links where possible. Do not move passwords, payment-card data, raw credentials, unnecessary identity data, or third-party secrets into JARVIS.

## Current build direction

1. Establish the cross-system portfolio registry.
2. Establish shared telemetry/event contracts.
3. Add the Wealth Protection adapter and dashboard module.
4. Normalize revenue and operating costs across projects.
5. Add portfolio-level contribution income and cash-flow views.
6. Add centralized exception routing.
7. Add agent health and automation economics.
8. Expand integrations only where they materially improve decision quality or reduce operator work.

Production integrations remain disabled until their credentials/connections and safety gates exist.
