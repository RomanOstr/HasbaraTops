# Israel Facebook Dialogue Lab

This repository is the canonical governance and execution layer for the Dialogue Lab. Repository Markdown owns governance, strategy, and reusable evidence. One SQLite database outside Git owns Case and Turn state.

The runtime performs no Google Drive or MCP operations.

## Architecture

```text
AGENTS.md                         canonical governance
docs/reply-strategy-guide.md     canonical cross-case strategy
docs/evidence-base.md            canonical reusable evidence
external SQLite database         canonical Cases and Turns
dialogue-lab CLI                 only canonical storage boundary
.agents/skills/                  model-driven analysis and reply workflows
```

`General responses` is protected and outside this workflow. The CLI exposes no operation for it.

## Deterministic boundary

Python and SQLite own URL parsing, identifiers, duplicate identity, schema constraints, lifecycle transitions, parent graphs, transactional writes, committed read-back, open-case summaries, strategy datasets, backups, and migration receipts.

The model owns interpretation, materially ambiguous parentage, reply drafting, fact-check judgment, and strategy analysis. Each canonical workflow ends in at most one high-level write command.

## Installation

```powershell
uv sync --frozen --extra dev
$env:DIALOGUE_LAB_DB = '<outside-repo>\dialogue-lab.sqlite3'
uv run dialogue-lab db-init --approved
uv run dialogue-lab doctor
```

`DIALOGUE_LAB_DB` must resolve outside the Git repository. `--database <path>` may override it and must appear before the subcommand.

Database initialization, imports, backups, and Case or Turn mutations require `--approved`. Read commands do not mutate state.

## High-level commands

```text
dialogue-lab doctor
dialogue-lab db-init --approved
dialogue-lab db-status
dialogue-lab db-backup --destination <outside-repo-path> --approved
dialogue-lab db-import <snapshot.json> --approved

dialogue-lab case-find --post-id <id> --root-comment-id <id>
dialogue-lab case-show --case-id <id>
dialogue-lab case-list-open
dialogue-lab strategy-dataset

dialogue-lab case-intake <payload.json> --date <YYYY-MM-DD> --approved
dialogue-lab case-followup --case-id <id> <payload.json> --approved
dialogue-lab case-record-posting --case-id <id> <payload.json> --approved
dialogue-lab case-close --case-id <id> <payload.json> --approved
```

The high-level write commands allocate identifiers, validate all affected records, write inside an immediate SQLite transaction, commit, reopen, and compare the committed records. Errors produce compact JSON on stderr and a nonzero exit code.

See [CLI payload contracts](docs/cli-payloads.md) for exact JSON shapes.

## Dialogue workflows

- Intake: `$dialogue-lab-intake`
- Follow-up: `$dialogue-lab-followup`
- Posting confirmation: `$dialogue-lab-posting`
- Closeout: `$dialogue-lab-closeout`
- Strategy review: `$dialogue-lab-strategy-review`

Skills use read commands automatically. They may pass `--approved` only after the user approves the exact canonical write. No skill publishes to Facebook.

## Migration

1. Prepare a UTF-8 JSON snapshot with `cases` and `turns` arrays using the exact payload contract.
2. Initialize an empty outside-Git database.
3. Create a verified empty backup.
4. Run `db-import` once after explicit approval.
5. Run `doctor`, compare counts and representative records, create a populated backup, and record `docs/migration-receipt.json.example` with actual values.

Import is atomic and only accepts an empty database. Duplicate Case IDs, duplicate `Post ID + Root Comment ID`, invalid enums, invalid URLs, missing parents, cycles, and foreign-key violations stop the transaction.

## Safety

- Never commit SQLite databases, journals, exports, backups, credentials, secrets, or public Facebook text.
- Never access Facebook unless explicitly requested; never post autonomously.
- Never overwrite a backup. Rollback restores a verified backup to a new path.
- Keep one canonical writer.

See [controlled rollout](docs/rollout.md) and [rollback](docs/rollback.md).

## Development

```powershell
uv run pytest
uv run ruff check .
uv run mypy
```

Tests use temporary SQLite databases and synthetic public text only.
