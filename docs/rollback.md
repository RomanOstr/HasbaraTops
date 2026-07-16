# Rollback checkpoint and procedure

## Pre-cutover checkpoint

1. Record the exact Manual version and Drive revision or modified state.
2. Record the Case Log schema signature and modified state.
3. Record the repository commit and validated check results.
4. After explicit approval, create local tag `pre-codex-cutover`.
5. Request named Drive versions where the live surface supports them.
6. After explicit approval, export offline backups of the four canonical files to an encrypted location outside the repository. Never include `General responses` unless explicitly requested.
7. Generate and verify a migration receipt.

After verified cutover, create local tag `codex-v1.0` only with explicit approval.

## Rollback

1. Obtain explicit user authorization.
2. Disable Codex writes and verify no operation is in progress.
3. Reconcile every Pending Sync record.
4. Restore or select the recorded Drive checkpoint when necessary.
5. Verify Manual revision, Case Log schema, Case Log modified state, and required records.
6. Re-enable exactly one writer.
7. Generate a rollback migration receipt.

Never leave Codex and the previous runtime writable at the same time.
