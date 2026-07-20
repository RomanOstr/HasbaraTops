# Synthetic evals

`cases/synthetic-cases.json` contains no real Case or Turn rows, participant names, or Facebook text.

- Deterministic assertions cover URL identity, identifier allocation, lifecycle, graph validation, SQLite schema and integrity, approval gates, committed read-back, and rollback behavior.
- Qualitative reply review covers claim alignment, one pivotal point, natural thread language, legal precision, face-saving correction, and silent-reader usefulness.
- Storage validation runs only against temporary local SQLite databases and never contacts an external service.
- Canonical writes, repository strategy edits, cutover, backups, tags, remote publication, and rollback require explicit approval.
