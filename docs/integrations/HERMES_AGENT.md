# Hermes Agent worker integration

Hermes Agent is the bounded execution-worker layer beneath JARVIS. It does not replace JARVIS, ChatGPT orchestration, source-system authority, or the Autonomy Control Plane.

## Topology

Eric -> ChatGPT/JARVIS -> OrchestrationGate -> Hermes worker -> isolated tools/runtime

Claude remains the independent second-brain reviewer through the existing second-brain integration.

## Runtime policy

Start Hermes with its **Blank Slate** setup. Keep direct business credentials out of Hermes during the pilot. Prefer an isolated Docker terminal backend. Enable the official Hermes API server with a bearer key and expose it only through a protected HTTPS endpoint.

Required Hermes settings:

- `API_SERVER_ENABLED=true`
- `API_SERVER_KEY=<random secret>`
- gateway running with `hermes gateway`

Required JARVIS environment:

- `HERMES_ENABLED=true` only after every activation check passes
- `HERMES_API_URL=https://<hermes-host>`
- `HERMES_API_KEY=<same secret>`
- `HERMES_MODEL=hermes-agent`

The bridge uses Hermes' documented OpenAI-compatible `POST /v1/chat/completions` endpoint. Non-loopback HTTP URLs, embedded URL credentials, invalid timeouts, and disabled runtimes fail closed before a network call.

## Initial authority

Phase 1 is dry-run and research/code assistance only. Hermes may inspect provided repositories/files in its isolated workspace and return proposed changes. External writes, publishing, money movement, trading, credential changes, destructive actions, and contract actions stay outside Hermes and must pass through JARVIS policy/approval controls.

## Activation checklist

1. Review the current official Hermes installer and calculate its SHA-256.
2. Run `HERMES_INSTALLER_SHA256=<reviewed-sha256> scripts/hermes_bootstrap.sh` on a persistent Linux host/VM.
3. Complete `hermes setup` using Blank Slate and configure a model with at least 64K context.
4. Enable the API server and create a bearer key.
5. Start `hermes gateway`.
6. Set JARVIS `HERMES_API_URL`, `HERMES_API_KEY`, and `HERMES_MODEL`.
7. Run `hermes doctor`.
8. Smoke-test `/v1/chat/completions`.
9. Run JARVIS unit tests.
10. Change `config/hermes-agent.json.enabled` and set `HERMES_ENABLED=true` only after the smoke test passes.
11. Add tools one at a time, preserving least privilege.

## Deployment note

Hermes is a long-running agent/gateway. JARVIS may remain on Vercel, but Hermes itself should run on a persistent worker host (or another supported persistent/serverless Hermes backend). Do not embed the long-running gateway into the ordinary JARVIS Vercel request lifecycle.
