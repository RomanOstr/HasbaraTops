---
name: dialogue-lab-intake
description: Start or identify an Israel Facebook Dialogue Lab case from a public post, root comment, screenshot, text, or Facebook URL. Use for new-case intake, duplicate-case detection, claim mapping, fact checking, and a first reply recommendation; canonical Drive writes remain approval-gated.
---

# Dialogue Lab Intake

## Required inputs

- Public post context and target root comment from text, screenshots, or supplied URLs.
- Any relevant preceding public turns. Never use profile-derived personal data.

## Workflow

1. Read `config/drive-files.toml`. Through the Google Drive plugin, read the complete live Operating Manual and record its version plus revision or modified state. Run `dialogue-lab manual-version` and stop write preparation if compatibility fails.
2. Read Case Log metadata, Cases/Turns headers, Data Dictionary enums/validations, and relevant current rows. Run `dialogue-lab schema-check` against the observed schema. Preserve the live schema.
3. Parse every supplied Facebook URL with `dialogue-lab parse-url`. Preserve the exact URL; never infer a parent solely from `reply_comment_id`.
4. Build `facebook:<Post ID>:<Root Comment ID>` with `dialogue-lab case-key`. Search Cases for that identity before allocating. If found, hand off to `$dialogue-lab-followup`.
5. Extract the post, target and preceding public turns, first recorded comment, current case-local participant reference, material claims, hidden assumption, hostility, evidence confidence, privacy issues, and supplied URLs. Store no names or profile links.
6. Load the live Strategy Guide and Evidence Base only as needed. Verify material current, historical, legal, military, statistical, and media-authenticity claims with current sources; separate fact, assessment, allegation, legal status, and moral judgment.
7. Produce the standard output below. Do not write exploratory or intermediate drafts.

## Canonical write gate

- Read automatically; write only after explicit user approval at a Manual-allowed lifecycle point.
- Immediately before a write, re-read relevant rows, unresolved Pending Sync, source revision state, and schema. Run the identifier, record, transition, graph, and source-consistency CLI checks.
- Send only a typed Case Log append/update request through the runtime connector. Never write `General responses`, the Strategy Guide, or the Evidence Base here.
- Read the exact row back and run `dialogue-lab verify-readback`. A connector success without a matching read-back is failure.
- On failure, show a complete PENDING SYNC record and block new Case ID allocation. Never post to Facebook.

## Output

Return, in order: `Case ID / Status`, `Claim Map`, `Recommended Reply`, `Shorter Version`, `Why This Approach`, `Fact Check`, `Conversational Potential`, `Log Tags`, and `Next Action`.

Use the Manual's exact Next Action line. The public reply must use the thread language, focus on one pivotal point, sound natural, remain useful to silent readers, offer a face-saving path where warranted, and never fabricate evidence.
