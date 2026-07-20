---
name: dialogue-lab-posting
description: Record a user's explicit confirmation that a Dialogue Lab reply was posted, using one deterministic SQLite transaction; this skill never publishes to Facebook.
---

# Dialogue Lab Posting Confirmation

## Required inputs

- Target Case ID and parent Turn ID.
- Exact wording actually published, even when it differs from the recommendation.
- Supplied permalink, identifiers, posting time, and optional Draft Turn ID.

## Workflow

1. Run `dialogue-lab doctor` and load the Case once with `case-show`.
2. Parse any supplied URL with `parse-url`; preserve it exactly and do not derive the immediate parent solely from `reply_comment_id`.
3. Prepare one Outgoing Posted Turn payload containing the exact published wording. Include `draft_turn_id` only when an existing Outgoing Draft must be marked Replaced.
4. Run exactly one `dialogue-lab case-record-posting --case-id <id> <payload> --approved` transaction. It allocates the Turn ID, validates the graph and lifecycle, writes atomically, and reads back the committed state.

## Safety

- Never publish, edit, or delete Facebook content.
- Never assume the posted text equals an earlier draft.
- Never access or write `General responses`.

## Output

Return only the compact command receipt plus exact-text and permalink preservation status.
