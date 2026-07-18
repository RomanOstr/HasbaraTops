# Synthetic evals

`cases/synthetic-cases.json` contains no real Case Log rows, participant names, or Facebook text.

- Deterministic assertions: URL identity, identifier allocation, lifecycle, graph, schema, Pending Sync, read-back, and source-consistency expectations are executable tests.
- Qualitative reply review: claim alignment, one pivotal point, natural thread language, legal precision, face-saving correction, and silent-reader usefulness require human or model review under the live Manual.
- Drive integration checks: connector reads, revision states, schema inspection, approval-gated writes, and read-back must run against the live sources and must never be inferred from synthetic results.
- Human approval: canonical writes, Strategy Guide edits, cutover, backups, tags, remote publication, and rollback require explicit approval.
