# Jarvis Access Broker

Before escalating any login or permission blocker to the owner, Jarvis must attempt safe access recovery in this order:

1. Reuse an already-active connector or authorized account.
2. Refresh an existing OAuth grant or token when the platform supports it.
3. Use a supported app authorization flow that can complete without owner interaction.
4. Use a narrowly scoped API token when one already exists or can be provisioned without exposing secrets or weakening security.
5. Use a service account or machine identity when the platform legitimately supports delegation for the requested task.
6. Escalate only when a human authorization ceremony, secret choice, MFA/passkey approval, CAPTCHA, legal acceptance, or another genuinely human-only action remains.

The broker follows least privilege and never bypasses MFA, passkeys, CAPTCHA, device approval, account security, rate limits, authorization boundaries, or platform terms. It must not reuse credentials across unrelated systems, fabricate tokens, exfiltrate secrets, hijack sessions, or impersonate the owner.

When escalation is unavoidable, the alert must describe what autonomous routes were attempted, why they failed, and the smallest owner action required. A simple “please log in” escalation is not acceptable unless the Access Broker has exhausted the safe alternatives above.
