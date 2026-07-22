# Synthetic evals

`cases/synthetic-cases.json` contains no real Case or Turn rows, participant names, or Facebook text.

- Deterministic assertions cover global Case-ID allocation, definitive Case lookup, multi-candidate root lookup, Turn duplicate identity, lifecycle, graph validation, schema-version-1 integrity, approved migration backups, committed read-back, and rollback behavior.
- Qualitative reply review covers claim alignment, one pivotal point, natural thread language, legal precision, face-saving correction, and silent-reader usefulness.
- Storage validation runs only against temporary local SQLite databases and never contacts an external service.
- Canonical writes, repository strategy edits, cutover, backups, tags, remote publication, and rollback require explicit approval.
