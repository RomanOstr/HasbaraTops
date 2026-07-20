---
name: dialogue-lab-intake
description: Start or identify an Israel Facebook Dialogue Lab case from supplied public content, perform deterministic duplicate detection, and prepare one approval-gated SQLite intake transaction.
---

# Dialogue Lab Intake

## Required inputs

- Public post context and target root comment from text, screenshots, or supplied URLs.
- Any relevant preceding public turns. Never use profile-derived personal data.

## Workflow

1. Run `dialogue-lab doctor` once for the configured database.
2. Parse every supplied Facebook URL with `dialogue-lab parse-url`; preserve exact URLs and never infer a parent solely from `reply_comment_id`.
3. Resolve `Post ID + Root Comment ID` with `dialogue-lab case-find`. If found, hand off to `$dialogue-lab-followup` without allocating or writing.
4. Extract the public context, case-local participant references, material claims, hidden assumption, hostility, evidence confidence, privacy state, and supplied URLs. Store no names or profile links.
5. Read repository strategy and evidence Markdown only as needed. Verify material current claims with authoritative sources and distinguish fact, assessment, allegation, legal status, and moral judgment.
6. Prepare one `case-intake` JSON payload containing the Case and initial public Turns. Do not persist exploratory drafts.
7. Return the standard output. After explicit approval, run exactly one `dialogue-lab case-intake <payload> --date <date> --approved` transaction and report its compact receipt.

## Output

Return, in order: `Case ID / Status`, `Claim Map`, `Recommended Reply`, `Shorter Version`, `Why This Approach`, `Fact Check`, `Conversational Potential`, `Log Tags`, and `Next Action`.

The public reply must use the thread language, focus on one pivotal point, sound natural, remain useful to silent readers, offer a face-saving path where warranted, and never fabricate evidence.
