# Controlled rollout

## Stage 1 — Local deterministic validation

Run the frozen dependency sync, unit tests, Ruff, mypy, CLI smoke checks, synthetic eval validation, and lock reproducibility checks. Use synthetic fixtures only.

## Stage 2 — Read-only Drive validation

Connect the Google Drive plugin. Read all four canonical sources, verify Manual compatibility, verify exact Case Log schema and formulas, confirm `General responses` classification, and record source revision states. Perform no writes.

## Stage 3 — Controlled write test

Only after explicit approval and only when the Manual permits it, perform one safe production Case Log write, read every field back, and record audit metadata. Do not create disposable test pollution. Reconcile the record only through an authorized canonical lifecycle action.

## Stage 4 — Shadow use

Run Codex alongside the previous workflow while exactly one system remains writable. Compare identity, turns, exact URLs, statuses, parent graphs, factual classifications, and reply outputs. Fix the producing implementation rather than patching isolated outputs. Do not duplicate canonical public text in shadow logs.

Use at least ten representative shadow cases unless fewer cases exist or the user explicitly approves less. Include new intake, duplicate intake, a branch, ambiguous parentage, posting confirmation, closure, hostility, a legal claim, and a failed-write simulation.

## Stage 5 — Cutover gate

Require zero duplicate-identity mismatches, URL corruption incidents, parent-graph failures, unverified writes, protected-file write attempts, and unresolved Pending Sync records. Require all deterministic tests, lint, and type checks to pass, successful read-only Drive validation, successful approved read-back write validation when exercised, the minimum shadow sample, and explicit user approval.

## Stage 6 — Cutover

Make Codex the only canonical writer, freeze the previous ChatGPT Project in reference mode, record the migration receipt, create the approved repository tag, and remain in single-writer mode. Re-enabling the old writer is an explicit rollback decision.

## Stage 7 — Optional private GitHub and CI

Only after explicit approval, create a private remote, push validated history, require pull-request checks, and enable secret/dependency scanning. CI must exclude canonical exports, audit logs, backups, and credentials and must never write to production Drive.

## Previous runtime modes

Reference mode may read historical conversations but may not allocate IDs, append turns, update lifecycle state, or write canonical files.

Rollback mode requires explicit authorization and the procedure in `docs/rollback.md`. Exactly one writer must remain enabled.
