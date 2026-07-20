# Controlled rollout

## Stage 1 - Local deterministic validation

Run unit tests, Ruff, mypy, CLI smoke checks, synthetic eval validation, and lock reproducibility checks. Use temporary SQLite databases only.

## Stage 2 - Canonical content preparation

Review repository governance, strategy, and evidence Markdown. Keep `General responses` outside the workflow unless the user explicitly names an exact action for it.

## Stage 3 - Empty database validation

After explicit approval, initialize a database outside Git, run `dialogue-lab doctor`, create a verified backup, and record its schema signature and integrity result.

## Stage 4 - Deterministic import

Prepare one JSON snapshot containing Cases and Turns. Run `db-import` once after explicit approval. The import must be atomic, preserve exact public text and URLs, reject duplicate identity, and pass committed count and integrity checks.

## Stage 5 - Shadow validation

Compare imported identities, turns, exact URLs, statuses, parent graphs, classifications, and representative high-level command results against the source snapshot. Fix the producing implementation instead of patching individual rows.

## Stage 6 - Cutover gate

Require zero duplicate identities, URL corruption incidents, graph failures, unverified writes, schema mismatches, or integrity failures. Require checks passed, a verified backup, a complete migration receipt, and explicit user approval.

## Stage 7 - Cutover

Set `DIALOGUE_LAB_DB` to the verified external database and use only high-level `dialogue-lab` commands for canonical Case and Turn operations. Keep one writer.

Rollback requires explicit authorization and `docs/rollback.md`.
