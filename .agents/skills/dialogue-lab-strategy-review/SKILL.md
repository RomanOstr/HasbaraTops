---
name: dialogue-lab-strategy-review
description: Review deterministic SQLite evidence across closed Israel Facebook Dialogue Lab cases and propose, but never apply, repository strategy-guide changes.
---

# Dialogue Lab Strategy Review

## Required inputs

- Review question, candidate strategy, or comparable-case criteria.
- At least three reasonably comparable closed cases; twenty closed cases for the first formal review.

## Workflow

1. Run `dialogue-lab doctor`, read `docs/reply-strategy-guide.md`, and load all closed Cases and Turns in one `dialogue-lab strategy-dataset` call.
2. Reject fewer than three reasonably comparable cases. Label reviews below twenty total closed cases as preliminary.
3. Compare topic, hostility, evidence confidence, reply length, thread position, and strategy. Separate commenter outcomes from silent-reader signals.
4. Report sample sizes, contradictory evidence, missing data, and confounders. Do not infer causation from correlation or treat one case as a reusable finding.
5. Distinguish supported findings, provisional hypotheses, and inconclusive results. Keep case-specific lessons in SQLite.
6. Draft the smallest exact Strategy Guide change only when evidence supports it. Do not edit the guide in this run; a separate explicit approval and reviewed repository change are required.

## Safety

- Never access or write `General responses`, and never post to Facebook.

## Output

Return review scope, closed-case count, comparable-case count, sample table, commenter outcomes, silent-reader signals, confounders, contradictory evidence, conclusion strength, and exact proposed Strategy Guide wording or `No change proposed`.
