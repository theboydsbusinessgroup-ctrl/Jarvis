# Wholesale Deal Engine Integration

JARVIS integrates with Wholesale Deal Engine as the portfolio orchestration and income-intelligence layer. The domain engine remains the source of truth for property and transaction operations.

## Module

**Wholesale Deal Engine**

JARVIS should display:

- Opportunities discovered
- Qualified opportunities
- Active seller negotiations
- Offers submitted/accepted
- Active contracts
- Contracts at risk
- Buyer matches
- Assignments pending
- Closings pending
- Realized assignment income
- Expected assignment income
- Net realized income
- Capital exposure
- Conversion rates
- Active exceptions
- Human-review queue
- Last scan/underwriting/buyer-match timestamps
- Engine and integration health

## Authority

JARVIS may prioritize, report, alert, and request safe/non-binding work. It must not bypass Wholesale Deal Engine authorization, legal/compliance controls, transaction-document controls, title/escrow holds, or financial controls.

JARVIS must never directly sign contracts, move transaction funds, change offer limits, or override a compliance hold.

## Event flow

Wholesale Deal Engine emits normalized deal lifecycle events and financial telemetry. JARVIS consumes those events for portfolio-level visibility, alerts, prioritization, forecasting, and cross-project income analysis.

JARVIS may return prioritized work requests such as fresh underwriting, buyer re-matching, market/source prioritization, or human-review escalation.

## Income reporting rule

Pipeline and expected assignment fees are forecasts, not realized income. JARVIS must show realized assignment income separately and subtract documented attributable transaction costs when calculating net realized income.

## Security

Use opaque deal/buyer/seller identifiers and deep links where practical. Keep sensitive PII, credentials, payment information, and transaction documents within their authorized domain systems.
