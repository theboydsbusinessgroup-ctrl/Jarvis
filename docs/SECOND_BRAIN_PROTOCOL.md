# Second Brain Protocol

## Purpose
Jarvis may consult a secondary model for independent review of consequential decisions. The secondary model is advisory; Eric retains final authority and Jarvis/ChatGPT remains the primary orchestration layer unless explicitly changed.

## Review modes

### Parallel review — preferred for consequential decisions
1. Define the problem and decision criteria without including another model's conclusion.
2. Send the same problem independently to the primary and secondary reasoning systems.
3. Collect structured verdicts.
4. Compare disagreements, evidence, assumptions, risk, cost, and reversibility.
5. Synthesize one recommended action or escalate only when human judgment is genuinely required.

Use parallel review for architecture, security, major spending, regulated workflows, production deployments, revenue-strategy changes, and other decisions with material downside.

### Adversarial review — preferred for implementation review
1. Primary system produces a concrete plan or patch.
2. Secondary model is instructed to attack assumptions and identify failure modes.
3. Primary system revises or defends the proposal.

Use this for code review, threat modeling, deployment plans, pricing logic, and complex debugging.

## Required secondary-brain output
- Decision: APPROVE / MODIFY / REJECT
- Top reason
- Material changes required
- Risk if ignored
- Human escalation required: YES / NO
- Confidence: LOW / MEDIUM / HIGH

## Cost control
Do not call a second model for routine low-risk tasks. Route only when independent reasoning is likely to materially improve outcome quality.

## Transport reality
A Claude consumer subscription does not itself create machine-to-machine communication with Jarvis. Automatic communication requires API/model-router access or another supported runtime. Until such a transport exists, human copy/paste may be used, but shared state should still remain canonical outside either chat.
