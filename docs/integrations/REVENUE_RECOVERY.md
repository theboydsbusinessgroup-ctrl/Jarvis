# Revenue Recovery integration

Jarvis consumes only a PII-safe aggregate snapshot from Revenue Recovery. Revenue Recovery remains authoritative for customer-level records, source evidence, contact policy, suppression decisions, drafting, and recovery verification.

Jarvis surfaces canonical opportunity count, ready/suppressed counts, identified recoverable value, freshness, blockers, and recommended actions. Identified recoverable value is displayed separately from verified portfolio revenue and must never be added to revenue totals.

The checked-in `data/revenue-recovery.json` is a point-in-time transport fixture representing the latest verified integration test. Production should refresh the same contract through an authenticated read-only telemetry path. The loader marks snapshots stale after 24 hours rather than pretending old data is live.

Jarvis cannot send recovery messages, override suppression, change customer records, or mark a recovery as won.
