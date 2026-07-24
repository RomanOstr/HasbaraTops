# Rollback checkpoint and procedure

## Pre-cutover checkpoint

1. Record the repository commit, schema version, schema signature, database integrity, row counts, and current Case-ID sequence.
2. Run the explicitly approved migration command with a new outside-Git backup destination; it must verify the legacy schema, locked source snapshot, and backup before writing.
3. Preserve its migration receipt with the pre-migration repository commit.

## Rollback

1. Obtain explicit user authorization and stop canonical writes.
2. Preserve the failed database for diagnosis; do not overwrite it.
3. Restore the verified backup to a new outside-Git path.
4. Use the recorded pre-migration repository commit, point `HASBARATOPS_DB` to the restored database, and run `HasbaraTops check`.
5. Verify schema version 1, integrity, Case count, Turn count, Case/Turn references, and the affected records before resuming one writer.

Never copy, restore, or overwrite a canonical database without explicit approval.
