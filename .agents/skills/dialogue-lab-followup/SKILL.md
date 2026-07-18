---
name: dialogue-lab-followup
description: Process a new public Facebook comment, reply, reaction, screenshot, text, or permalink in an existing Israel Facebook Dialogue Lab case. Use to extend the turn graph, resolve parentage with explicit confidence, update Active Exchange state, and recommend the next reply.
---

# Dialogue Lab Follow-up

## Required inputs

- Existing Case ID or enough Post ID + Root Comment ID data to resolve it.
- Exact new public turn or reaction, supplied URL, observed time, and any visible parent context.

## Workflow

1. Read the complete live Manual and record its compatible version and revision state. Read the live Case Log schema and run `dialogue-lab schema-check`.
2. Parse supplied URLs with `dialogue-lab parse-url`, preserve each exact URL, resolve canonical identity, and load the existing Case plus every relevant Turn.
3. Assign or reuse only `P1`, `P2`, … or `USER`. Identify the direct parent from visible context or user confirmation; record Parent Confidence. Ask only when ambiguity materially changes the reply.
4. Build the candidate incoming Turn, then run `dialogue-lab validate-turn` and `dialogue-lab validate-parent-graph`. Multiple children may share a parent. Show a compact Thread Map when the graph is branched.
5. Load the live Strategy Guide and Evidence Base as needed, verify material claims, and answer the operative claim without treating private planning as public context.
6. Produce the standard reply output. Ignore incidental abuse; use `no_engagement` for credible threats, doxxing, calls for violence, spam, or no testable claim.

## Canonical write gate

- Reads are automatic. Any Case/Turn append or update requires explicit approval and a Manual-allowed lifecycle action.
- Before writing, re-read relevant rows, Pending Sync, source states, and schema; run source-consistency and case-local Turn ID allocation on the fresh rows.
- After the runtime connector call, read the Case and Turn back and run `dialogue-lab verify-readback`.
- On write or verification failure, show a complete PENDING SYNC record and do not claim Drive was updated. Never post to Facebook or write protected documents.

## Output

Return, in order: `Case ID / Status`, optional `Thread Map`, `Claim Map`, `Recommended Reply`, `Shorter Version`, `Why This Approach`, `Fact Check`, `Conversational Potential`, `Log Tags`, and `Next Action`.

Use the Manual's exact Next Action line and the Facebook thread's language.
