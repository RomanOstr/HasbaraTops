---
name: dialogue-lab-followup
description: Process supplied public content in an existing Israel Facebook Dialogue Lab case, resolve parentage, and prepare one approval-gated SQLite follow-up transaction.
---

# Dialogue Lab Follow-up

## Required inputs

- Existing Case ID or enough Post ID + Root Comment ID data to resolve it.
- Exact new public turn or reaction, supplied URL, observed time, and visible parent context.

## Workflow

1. Run `dialogue-lab doctor`, resolve the Case with `case-find` when needed, then load it once with `case-show`.
2. Parse supplied URLs with `parse-url`, preserve each exact URL, and confirm the Case identity.
3. Assign or reuse only `P1`, `P2`, ... or `USER`. Resolve the direct parent from visible context or user confirmation and retain Parent Confidence; ask only when ambiguity changes the reply.
4. Build one incoming Turn payload. The `case-followup` transaction allocates the Turn ID, validates the complete parent graph, appends the Turn, updates Case state, commits, and reads back.
5. Read repository strategy and evidence Markdown only as needed, verify material claims, and answer the operative claim without treating private planning as public context.
6. Return the standard output. After explicit approval, run exactly one `dialogue-lab case-followup --case-id <id> <payload> --approved` transaction and report its compact receipt.

## Output

Return, in order: `Case ID / Status`, optional `Thread Map`, `Claim Map`, `Recommended Reply`, `Shorter Version`, `Why This Approach`, `Fact Check`, `Conversational Potential`, `Log Tags`, and `Next Action`.

Use the Facebook thread's language. Ignore incidental abuse; use `no_engagement` for credible threats, doxxing, calls for violence, spam, or no testable claim.
