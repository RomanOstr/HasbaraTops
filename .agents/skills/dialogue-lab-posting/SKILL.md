---
name: dialogue-lab-posting
description: Record a user's explicit confirmation that a Dialogue Lab reply was posted to Facebook. Use when the user says a reply was posted and supplies or confirms the exact published wording, permalink, identifiers, or posting time. This skill records state; it never publishes to Facebook.
---

# Dialogue Lab Posting Confirmation

## Required inputs

- Target Case ID and parent Turn ID.
- Exact wording actually published, even when it differs from the recommendation.
- Supplied permalink, IDs, and posting time when available.

## Workflow

1. Read the complete live Manual, verify compatibility, and record its revision state. Read and validate the live Case Log schema.
2. Resolve the case and parent turn. Parse any supplied URL with `dialogue-lab parse-url`; preserve it exactly and do not derive the immediate parent solely from `reply_comment_id`.
3. Find an approved Draft row representing the posted reply. Update that row when appropriate; otherwise prepare a new Outgoing Posted Turn. Preserve exact published wording without rewriting it.
4. Run `dialogue-lab validate-turn`, `dialogue-lab validate-transition`, and `dialogue-lab validate-parent-graph`. Update Case timestamps and status as the Manual requires.
5. Re-read relevant rows, unresolved Pending Sync, source revisions, and schema. Run `dialogue-lab source-consistency` before the approval-gated connector write.
6. Read every written field back and run `dialogue-lab verify-readback`.
7. If writing or read-back fails, show a complete PENDING SYNC record and state that Drive was not verified.

## Safety

- Never publish, edit, or delete Facebook content.
- Never assume the posted text equals an earlier draft.
- Never write `General responses`, the Strategy Guide, or the Evidence Base.
- Never treat connector acknowledgement as successful posting confirmation without matching Case Log read-back.

## Output

Return a compact posting receipt containing Case ID, Turn ID, state, exact-text verification, URL/ID preservation status, Manual version and revision, source-consistency result, and read-back result.
