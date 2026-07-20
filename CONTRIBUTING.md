# Contributing

Open an issue before substantial changes. Keep changes narrowly scoped, preserve
the local SQLite transaction boundary, and never commit databases, exports,
backups, credentials, secrets, or public Facebook content.

Before proposing a change, run:

```powershell
uv run pytest
uv run ruff check .
uv run mypy
uv run dialogue-lab --database <external-test-database> doctor
```

Contributions are accepted only under the repository's proprietary license.
