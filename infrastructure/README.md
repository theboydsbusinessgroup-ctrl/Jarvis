# Jarvis Shared Automation Core

This directory is the common automation substrate for the Boyd portfolio.

## Phase 1 services
- PostgreSQL: shared operational state
- n8n: event/workflow orchestration
- changedetection.io: opportunity and competitor monitoring
- Metabase: portfolio dashboards

## Architecture rule
Jarvis is the command/control plane. Revenue repos remain independent domain services. Shared scheduling, browser jobs, scraping jobs, notifications, observability and state should be exposed as reusable services instead of copied into each revenue repo.

## Next integrations
1. Playwright worker for deterministic browser automation.
2. Crawlee worker for compliant public-web collection.
3. Browser Use fallback worker for reasoning-heavy browser tasks.
4. Langfuse observability.
5. Dify agent workflows only where they reduce custom agent code.
6. PostHog for funnel/product analytics.

## Safety / autonomy
- No secrets in Git.
- High-impact financial actions remain separately permissioned.
- Browser workers must respect site authorization, access controls, rate limits and applicable terms.
- Human approval gates should be configurable per workflow.

## Start locally
Copy `.env.example` to `.env`, replace placeholder secrets, then run:

`docker compose -f infrastructure/docker-compose.yml up -d`

This commit intentionally does not contain production credentials or automatically expose services to the public internet.
