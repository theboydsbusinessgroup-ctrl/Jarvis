# Second-Brain Runtime

Jarvis exposes a bounded advisory endpoint at `POST /api/second-brain`.

## What it does
1. Reads only the canonical files listed in `src/integrations/second_brain.py` from the private `Jarvis-State` repository.
2. Builds a minimal context packet around the submitted task, decision criteria, evidence, and review mode.
3. Sends the packet to the configured Claude model through OpenRouter.
4. Returns Claude's structured advisory response and usage metadata.

## What it does not do
- It cannot publish, spend, trade, sign, delete, transfer funds, or write back to canonical state.
- It does not expose GitHub or OpenRouter secrets in responses.
- Claude recommendations do not become canonical state automatically.

## Required deployment secrets
These must be configured in the deployment environment and never committed to GitHub:

- `GITHUB_STATE_TOKEN` — narrowly scoped read access to `Jarvis-State`.
- `OPENROUTER_API_KEY` — OpenRouter API key funded for Claude calls.

Optional settings:
- `JARVIS_STATE_OWNER` (default `theboydsbusinessgroup-ctrl`)
- `JARVIS_STATE_REPO` (default `Jarvis-State`)
- `JARVIS_STATE_REF` (default `main`)
- `JARVIS_SECOND_BRAIN_MODEL` (default `anthropic/claude-sonnet-5`)

## Review modes
- `parallel`: Claude receives a neutral task without ChatGPT's conclusion.
- `adversarial`: the evidence field may include a proposed plan for Claude to attack.

## Security boundary
The runtime remains advisory-only. Any future write-back mechanism must be separately authenticated, policy-checked, auditable, and idempotent.
