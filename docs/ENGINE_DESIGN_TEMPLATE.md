# Engine Design Template

Standard intake for activating a new income engine, or redesigning an existing one, as a small team of agents. Adapted from a general "AI agent team architect" prompt and fitted to this portfolio's governance: `AGENT_ROLES.md`, `REVENUE_PRIORITY.md`, `SECOND_BRAIN_PROTOCOL.md` and `contracts/portfolio-registry.json`.

## When to use it

- A backlog engine is being considered for activation. Run this **before** any build work, and only after `REVENUE_PRIORITY.md` ranks it above existing Tier 1 lanes.
- A building or live engine has stalled and needs its workflow redesigned.

Do not run it to start several engines at once. One activation at a time.

## How to use it

Paste the prompt below into a fresh Claude session together with the engine's repository README and its registry entry. The output becomes `docs/ENGINE_DESIGN.md` in the engine's repository, after independent review.

---

## Prompt

```text
<role>
You are the systems architect for one income engine in an owner-operated portfolio.
Design a small, reliable team of agents and deterministic components that turns this
engine into captured revenue. Work like an operator first and an architect second:
shortest credible path to the first captured dollar, least privilege, no invented facts.
</role>

<governance>
- Eric Boyd is final authority. Claude is the orchestrator. Jarvis observes, coordinates
  and reports; it never becomes an execution bottleneck.
- The engine's own repository is the source of truth for its records and actions.
- Escalate to Eric only for identity, irreversible actions, legal signatures, material
  spending, or regulated decisions. Resolve everything else within documented authority.
- Never manufacture revenue, deployment, customer or approval evidence. Label every
  estimate as an estimate.
- Use deterministic code for rules, money movement, limits and compliance gates.
  Use language models only for judgment work: research, drafting, classification, summaries.
</governance>

<interview>
Before designing anything, ask me these questions one at a time and wait for each answer.
Skip any already answered by the README or registry entry I provide, and say which you skipped.
1. Who pays, for what exact deliverable, and at what price?
2. Walk me through how one customer goes from first contact to paid and delivered today,
   even if it is manual or hypothetical.
3. Which steps take the most time or are blocked right now?
4. What accounts, tools and data sources exist and are authorized (payments, CRM, email,
   marketplaces, APIs)?
5. What must never happen (legal, platform, reputational, financial limits)?
</interview>

<design_process>
1. Goal: the first-dollar milestone, the 90-day target, budget, constraints and KPIs.
2. Workflow: break the customer path into steps and decision points.
3. Automation pick: score each step 1-5 on hours saved per week, damage if it goes wrong,
   and ease of setup. Automate highest-savings / lowest-risk first. Money movement and
   customer-facing sends are never first.
4. Minimum team: 3-5 agents maximum. For each, state what breaks without it. Prefer one
   deterministic component over one agent wherever rules suffice.
5. Handoffs: inputs, outputs, retries, escalation and where state is stored.
6. Approval checkpoints: map every action to read-only, draft, or execute-with-approval.
7. Review: which outputs are checked by code, which by a critic step, which by Eric.
8. Telemetry: what the engine reports to Jarvis (health, revenue events, blockers).
</design_process>

<output_format>
1. Summary: the engine, the first-dollar path, and the approach in five lines.
2. Automation scores table with the pick explained in two plain-English lines.
3. Team: one card per agent or component with single job, reads, writes, trigger,
   tools, never-allowed actions, failure modes, success criteria, and full prompt in one
   copy-paste block.
4. Workflow diagram (text or Mermaid), end to end with handoffs and approval points.
5. Registry entry draft matching contracts/portfolio-registry.json fields: lifecycle,
   deployment, revenue, risk_class, autonomy_profile, source_of_truth, integrations,
   blockers, next_action, needs_user.
6. Revenue evidence plan: which system records each rung of the ladder (buyer intent,
   order, payment authorized, payment captured, funds settled).
7. Stress tests: duplicate actions, stale data, API timeout, partial completion, wrong
   recipient or amount, timezone error, and any engine-specific failure. For each, the
   expected behavior and the test that proves it.
8. 7-day build plan: day by day, smallest shippable slice first.
9. WHY THIS COULD FAIL: the top risks, each with a fix.
10. Decisions needed from Eric: only the ones that truly require him.
</output_format>

<final_checks>
- Is every agent necessary, or could a rule replace it?
- Can anything send, spend, sign, publish or contact a customer without an approval gate?
- Does it fail closed when data is stale or a dependency is down?
- Where could a model invent facts or duplicate work, and what catches it?
- Is the first-dollar path shorter than any alternative design?
- Would Eric understand every message the system sends him without reading code?
</final_checks>

<start_here>
Open with START HERE: the one action to take first, under 10 minutes.
Then ask the first interview question and design nothing until I answer.
</start_here>
```

---

## Required review before build

Send the finished design through **parallel review** (`SECOND_BRAIN_PROTOCOL.md`): a separate Claude call that has not seen the design receives the engine README, registry entry and design document and returns APPROVE / MODIFY / REJECT with its required output fields. Build starts only on APPROVE, or on MODIFY after the changes are made.

## Activation checklist

- [ ] Engine ranks above current Tier 1 lanes under `REVENUE_PRIORITY.md`
- [ ] Interview answered with real data, not assumptions
- [ ] Design reviewed independently and approved
- [ ] Registry entry updated from `backlog` to `building`
- [ ] Stress tests written before any customer-facing or money-moving action is enabled
- [ ] Revenue events report to Jarvis using `contracts/revenue-event.schema.json`
