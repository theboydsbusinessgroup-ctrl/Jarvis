# Portfolio readiness monitoring

`python scripts/check_portfolio_health.py --output /tmp/portfolio-health.json`
checks four public service GET endpoints and the latest main-branch YouTube
publishing workflow concurrently with bounded timeouts. It performs
no checkout, payment, publishing, outreach, or credential-bearing requests.

The GitHub workflow runs hourly after merge to the default branch, or manually.
Each run saves a seven-day artifact. Required-field failures or unavailable /
malformed responses fail the job. Known setup gates and stale recovery telemetry
are reported as attention rather than falsely reporting those systems ready.
Only configured readiness fields are preserved in the artifact.

The YouTube check fails on a failed/cancelled publication or evidence older than
48 hours. An in-progress run is attention, never an asserted success. The hourly
job writes a readable Actions summary and preserves its JSON artifact.

`GET /api/readiness` exposes the same sanitized live checks to the dashboard.
Results are cached in memory for at most two minutes and include the observation
time. The dashboard displays these separately from dated registry plans. This
avoids treating a healthy website or a successful monitor run as evidence that
publishing, payments, delivery or all portfolio systems are ready.

The productized service check requires an enabled payment gate and reachable
order database. This is an operational check, not proof of captured payment,
settlement, customer delivery, or profitability.

The owner-authenticated revenue endpoint reads the Productized AI receipt feed
when configured. Unconnected or unavailable totals remain `UNVERIFIED`.
Its receipt coverage is limited to that service; it is not total portfolio revenue.
Do not interpret an empty in-memory ledger as observed zero portfolio revenue.

This monitor does not write back into the registry. Dated registry observations
remain snapshots. A later durable telemetry implementation must preserve provider
event IDs, test/live distinctions, refunds, observed timestamps and exact authority.

Second-brain calls require the existing owner session or owner bearer credential
and are rate-limited locally. Shared rate/cost limits are still required before
enabling substantial usage across multiple serverless instances.
