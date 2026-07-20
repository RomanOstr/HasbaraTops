# Contributing

Open an issue before substantial changes. Keep changes narrowly scoped, preserve
the Google Drive canonical-source boundary, and never commit credentials,
canonical document bodies, Case Log exports, or public Facebook content.

Before proposing a change, run:

```powershell
uv run pytest
uv run ruff check .
uv run mypy
uv run dialogue-lab doctor
```

Contributions are accepted only under the repository's proprietary license.
