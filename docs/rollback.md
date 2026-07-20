# Rollback checkpoint and procedure

## Pre-cutover checkpoint

1. Record the repository commit, schema version, schema signature, database integrity, and row counts.
2. After explicit approval, create a consistent SQLite backup outside Git and verify it with `db-status`.
3. Generate and verify a migration receipt.

## Rollback

1. Obtain explicit user authorization and stop canonical writes.
2. Preserve the failed database for diagnosis; do not overwrite it.
3. Restore the verified backup to a new outside-Git path.
4. Point `DIALOGUE_LAB_DB` to the restored database and run `dialogue-lab doctor`.
5. Verify schema, integrity, Case count, Turn count, and the affected records before resuming one writer.

Never copy, restore, or overwrite a canonical database without explicit approval.
