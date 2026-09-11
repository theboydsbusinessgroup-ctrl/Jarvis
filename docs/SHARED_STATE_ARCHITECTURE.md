# Shared State Architecture

## Objective
Prevent ChatGPT, Claude, Jarvis, and specialist agents from accumulating conflicting versions of project truth.

## Principle
Models reason over shared state; models are not the authoritative database.

## Canonical state layers
1. **Operating protocols** — durable behavioral and safety rules.
2. **Project registry** — project identity, owner, repository, lifecycle state, and current priority.
3. **Current status** — only verified state such as BUILT, CONNECTED, TESTED, DEPLOYED, LIVE, or REVENUE-PRODUCING.
4. **Decision log** — consequential decisions, date, rationale, and superseded decisions.
5. **Revenue priorities** — active lanes, blockers, next monetization action, evidence.
6. **Agent roles** — responsibilities, escalation rules, and permission boundaries.

## Confidentiality boundary
This Jarvis repository is public. Do **not** store private user memory, credentials, financial details, sensitive customer data, secrets, authentication material, or confidential operating state here.

Confidential shared state must live in a private repository or other access-controlled store. Public documentation may describe schemas and protocols only.

## Status honesty
Never collapse the following states:
- PLANNED
- BUILT
- CONNECTED
- TESTED
- DEPLOYED
- LIVE
- REVENUE-PRODUCING

Every dashboard or agent report should preserve these distinctions.

## Context packet
When an external model is called programmatically, Jarvis should assemble a minimal context packet containing only:
- relevant operating rules
- relevant project status
- relevant decisions
- task-specific evidence
- requested output schema

Do not send the entire memory corpus by default.

## Write-back rule
A model recommendation does not become canonical state automatically. Verified execution results and approved consequential decisions may be written back by the orchestration layer with provenance and timestamp.
