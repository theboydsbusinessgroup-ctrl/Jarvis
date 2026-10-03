# Portfolio readiness monitoring

`python scripts/check_portfolio_health.py --output /tmp/portfolio-health.json`
checks four public GET endpoints concurrently with bounded timeouts. It performs
no checkout, payment, publishing, outreach, or credential-bearing requests.

The GitHub workflow runs hourly after merge to the default branch, or manually.
Each run saves a seven-day artifact. Required-field failures or unavailable /
malformed responses fail the job. Known setup gates and stale recovery telemetry
are reported as attention rather than falsely reporting those systems ready.
Only configured readiness fields are preserved in the artifact.

The productized service check requires an enabled payment gate and reachable
order database. This is an operational check, not proof of captured payment,
settlement, customer delivery, or profitability.

The dashboard's revenue endpoint has no durable authoritative revenue feed.
Its status is now `not_connected`, and the dashboard labels it `UNVERIFIED`.
Do not interpret an empty in-memory ledger as observed zero portfolio revenue.

This monitor does not write back into the registry. Dated registry observations
remain snapshots. A later durable telemetry implementation must preserve provider
event IDs, test/live distinctions, refunds, observed timestamps and exact authority.

Second-brain calls require the existing owner session or owner bearer credential
and are rate-limited locally. Shared rate/cost limits are still required before
enabling substantial usage across multiple serverless instances.
