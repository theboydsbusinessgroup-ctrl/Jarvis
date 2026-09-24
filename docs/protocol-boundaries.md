# Orchestration and protocol boundaries

JARVIS uses two different boundaries for two different jobs:

- **MCP boundary**: tools and data sources.
- **A2A boundary**: agent-to-agent delegation.

This is a contract boundary, not a requirement to replace every existing integration immediately.

## Delegation policy

The current pilot defaults are:

- maximum parallel workers: 4
- maximum delegation depth: 2
- allowed delegated roles: specialist, reviewer
- required context: task identity, objective, constraints, authority context, and evidence references

Delegation is blocked when required context is missing or the worker/depth budget is exceeded.

Before a task is delegated, JARVIS fingerprints the preserved context. The receiving workflow can verify that material constraints and authority context did not silently change.

## Why this exists

More agents are not automatically more reliable. The orchestration gate treats additional workers as a bounded resource and preserves critical context across delegation.

## Rollout

1. Keep existing direct integrations working.
2. Require new tool/data adapters to implement the MCP adapter contract.
3. Require new agent-to-agent integrations to implement the A2A adapter contract.
4. Pilot the boundary on one specialist/reviewer workflow.
5. Measure latency, task success, context loss, retries, and operator intervention before expanding it.

No live external write permission is granted by these protocol contracts.
