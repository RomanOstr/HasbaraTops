# Controlled rollout

## Stage 1 - Local deterministic validation

Run unit tests, Ruff, mypy, CLI smoke checks, synthetic eval validation, and lock reproducibility checks. Use temporary SQLite databases only.

## Stage 2 - Canonical content preparation

Review repository governance, strategy, and evidence Markdown. Keep `General responses` outside the workflow unless the user explicitly names an exact action for it.

## Stage 3 - Empty database validation

After explicit approval, initialize a database outside Git, run `dialogue-lab check`, create a verified backup, and record its schema signature and integrity result.

## Stage 4 - Deterministic import or identity migration

For an empty database, prepare one JSON snapshot containing Cases and Turns and run `db-import` once after explicit approval. For an existing schema-version-1 database, run `db-migrate-identity` with an explicitly approved outside-Git backup destination. The operation must be atomic, preserve exact public text, URLs, Turn graphs, and schema version 1, assign `Case-NNN` in stable creation/allocation order, and pass committed mapping, count, and integrity checks.

## Stage 5 - Shadow validation

Compare Case IDs, Turns, exact URLs, statuses, parent graphs, classifications, and representative high-level command results against the source state. Verify explicit Case lookup, multi-candidate root lookup, and both Turn duplicate paths. Fix the producing implementation instead of patching individual rows.

## Stage 6 - Cutover gate

Require zero duplicate identities, URL corruption incidents, graph failures, unverified writes, schema mismatches, or integrity failures. Require checks passed, a verified backup, a complete migration receipt, and explicit user approval.

## Stage 7 - Cutover

Set `DIALOGUE_LAB_DB` to the verified external database and use only high-level `dialogue-lab` commands for canonical Case and Turn operations. Keep one writer.

Rollback requires explicit authorization and `docs/rollback.md`.
