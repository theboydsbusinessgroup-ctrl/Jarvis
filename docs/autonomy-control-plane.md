# Autonomy Control Plane v1

JARVIS now has a shared, fail-closed execution boundary for connector and tool calls.

## Flow

```
agent / workflow
  -> propose exact action
  -> resolve tool boundary
  -> deterministic policy decision
  -> checkpoint payload + workflow state
  -> approval when required
  -> reliable connector execution
  -> persist outcome
  -> resume workflow
```

## Rules

1. Every connector operation maps to a concrete tool key such as `gmail.send` or `github.commit`.
2. Unknown tools default to RED and require approval.
3. Prohibited policy actions cannot be overridden by approval.
4. Approval records preserve the exact payload and workflow state that was reviewed.
5. Retries reuse one idempotency key.
6. Successful operations are replay-safe: a duplicate execution request returns the stored result instead of firing again.
7. Authentication/permission failures and malformed/partial responses fail closed.
8. Only rate limits, timeouts, and transient server failures are retried, with bounded exponential backoff.
9. The current JSON checkpoint adapter is suitable for tests and persistent single-node deployments. Serverless/live production writes require a shared durable backend before enablement.
10. Live connector writes remain disabled until the connector is explicitly wired through this layer and its provider-specific contract tests pass.

## Risk examples

- GREEN: read/search/analyze/report.
- YELLOW: reversible branch commits, drafts, preview deploys, policy-gated production deploys.
- RED: external sends, money movement, destructive operations, merges to protected/default branches, security changes.

Risk classification is not itself authority. The existing autonomy policy remains the final deterministic policy source.

## Connector contract test matrix

Every live connector should prove:

- authentication success and expired-auth behavior
- authorization failure behavior
- rate-limit handling
- timeout handling
- server-error handling
- malformed response rejection
- partial response rejection
- duplicate/retry idempotency
- end-state verification after mutation

Fault injection should run before a connector is promoted from read-only or dry-run to live write authority.
