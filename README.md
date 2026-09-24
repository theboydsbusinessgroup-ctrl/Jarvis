# JARVIS

## Governance and command structure

Effective September 19, 2026, the portfolio command structure is:

1. **Eric Boyd — principal and final authority**
2. **ChatGPT — main brain, lead business-development and management orchestrator**
3. **JARVIS — operating interface, monitoring, reporting, and connective tissue**
4. **Domain systems, agents, contractors, and tools — execution under their documented authority boundaries**

Perplexity is retired from the operating team at Eric Boyd's direction. Do not route tasks, research, reviews, approvals, escalations, or context packets to Perplexity; do not make any work depend on its subscription or availability. ChatGPT owns research and review coordination using available authorized tools, with unresolved consequential decisions escalated to Eric. This supersedes earlier Perplexity consultation requirements. No replacement paid service is authorized by this change.

Verified repositories, deployments, integrations, and system-of-record documents supersede unsupported status claims made in conversation. JARVIS must not become an execution bottleneck: revenue-producing work continues through each domain system while JARVIS observes, coordinates, and reports.

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
- Wealth Management Protection Protocol / Digital Estate Protection
- **Revenue Recovery Engine**

### Revenue Recovery module

Revenue Recovery is a first-class portfolio income engine. Its repository remains the source of truth for lead/customer opportunity records, recovery actions, attribution, reconciliation, and compliance state.

JARVIS should surface:

- active clients
- recovery pipeline value
- ready recovery opportunities
- qualified opportunities
- verified recovered revenue
- recovery fees
- contribution income
- client conversion/recovery rate
- average recovered value
- agent execution health
- human-review queue
- suppression/opt-out counts
- integration health
- data freshness
- last successful recovery run

JARVIS should never bypass Revenue Recovery suppression, compliance, attribution, or authority controls.

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
11. Connector actions pass through a shared tool policy boundary; unknown tools fail closed.
12. Approval-required actions persist the exact proposed payload and workflow checkpoint before review, then resume from that checkpoint.
13. Mutating connector retries reuse one idempotency key and must pass provider-specific reliability tests before live-write authority is enabled.
14. Agent delegation is bounded by worker-count and delegation-depth policy; critical context is fingerprinted and preserved.
15. MCP is the tool/data boundary; A2A is the agent-to-agent boundary. Transport choice never expands authority.

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

### Revenue Recovery

Dedicated view for recovery pipeline, verified recovered revenue, contribution income, recovery rate, client health, agent execution, suppression/opt-out health, and human exceptions. Customer-level data stays in Revenue Recovery; JARVIS receives only required operational telemetry.

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

## Revenue Recovery integration contract

The Revenue Recovery repository defines the canonical telemetry and authority contract in `docs/jarvis-integration.md`. JARVIS should consume verified events and never directly execute customer-contact or attribution actions.

## Current build direction

1. Establish the cross-system portfolio registry.
2. Establish shared telemetry/event contracts.
3. Add the Wealth Protection adapter and dashboard module.
4. Add the Revenue Recovery adapter and dashboard module.
5. Normalize revenue and operating costs across projects.
6. Add portfolio-level contribution income and cash-flow views.
7. Add centralized exception routing.
8. Add agent health and automation economics.
9. Expand integrations only where they materially improve decision quality or reduce operator work.
10. Promote connectors from read-only/dry-run only after the Autonomy Control Plane and connector reliability contract tests pass.
11. Pilot MCP/A2A protocol boundaries on one specialist/reviewer workflow and expand only when measured reliability improves.

Production integrations remain disabled until their credentials/connections and safety gates exist.
