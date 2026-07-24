---
name: hasbaratops-intake
description: Start or identify a HasbaraTops case from supplied public content, resolve Case-ID or root candidates, and prepare one approval-gated SQLite intake transaction.
---

# HasbaraTops Intake

## Required inputs

- Public post context and target root comment from text, screenshots, or supplied URLs.
- Any relevant preceding public turns. Never use profile-derived personal data.

## Workflow

1. Parse every supplied Facebook URL with `HasbaraTops parse-url`; preserve exact URLs and never infer a parent solely from `reply_comment_id`.
2. Use an explicitly supplied Case ID as definitive. Otherwise run `HasbaraTops case-find` by `Post ID + Root Comment ID`, treat every result as a candidate, and compare its Turn graph with the supplied reply branch. Hand off an identified existing Case to `$hasbaratops-followup`; an unmatched branch may become a new Case even when the Facebook root already has candidates.
3. Extract the public context, case-local participant references, material claims, hidden assumption, hostility, evidence confidence, privacy state, and supplied URLs. Store no names or profile links.
4. Read repository strategy and evidence Markdown only as needed. Verify material current claims with authoritative sources and distinguish fact, assessment, allegation, legal status, and moral judgment.
5. Prepare one `case-intake` JSON payload containing the Case and initial public Turns. Do not persist exploratory drafts.
6. Return the standard output. After explicit approval, run `HasbaraTops check`; if it passes, run exactly one `HasbaraTops case-intake <payload> --approved` transaction and report its compact receipt.

## Output

Return, in order: `Case ID / Status`, `Claim Map`, `Recommended Reply`, `Shorter Version`, `Why This Approach`, `Fact Check`, `Conversational Potential`, `Log Tags`, and `Next Action`.

The public reply must use the thread language, focus on one pivotal point, sound natural, remain useful to silent readers, offer a face-saving path where warranted, and never fabricate evidence.
