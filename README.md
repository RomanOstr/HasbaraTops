# Israel Facebook Dialogue Lab

This repository is the canonical governance and execution layer for the Dialogue Lab. Repository Markdown owns governance, strategy, and reusable evidence. One SQLite database outside Git owns Case and Turn state.

The runtime reads repository Markdown and the configured SQLite database only.

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
uv run dialogue-lab check
```

`DIALOGUE_LAB_DB` must resolve outside the Git repository. `--database <path>` may override it and must appear before the subcommand.

Database initialization, imports, backups, and Case or Turn mutations require `--approved`. Read commands do not mutate state.

## High-level commands

```text
dialogue-lab check
dialogue-lab db-init --approved
dialogue-lab db-status
dialogue-lab db-backup --destination <outside-repo-path> --approved
dialogue-lab db-import <snapshot.json> --approved
dialogue-lab db-migrate-identity --backup-destination <outside-repo-path> --approved

dialogue-lab case-find --case-id <Case-NNN>
dialogue-lab case-find --post-id <id> --root-comment-id <id>
dialogue-lab case-show --case-id <id>
dialogue-lab case-split-branch --case-id <id> --branch-root-turn-id <turn-id> --new-case-title <title> --new-topic <topic> --backup-destination <outside-repo-path> --approved
dialogue-lab case-list-open
dialogue-lab strategy-dataset

dialogue-lab case-intake <payload.json> --approved
dialogue-lab case-followup --case-id <id> <payload.json> --approved
dialogue-lab case-record-posting --case-id <id> <payload.json> --approved
dialogue-lab case-close --case-id <id> <payload.json> --approved
```

The high-level write commands allocate identifiers, validate all affected records, write inside an immediate SQLite transaction, commit, reopen, and compare the committed records. Errors produce compact JSON on stderr and a nonzero exit code.

See [CLI payload contracts](docs/cli-payloads.md) for exact JSON shapes.

## Identity model

`case_id` is the definitive Case key. Case IDs use `Case-NNN` and are allocated from one global sequence; dates and Facebook identifiers are not part of the key. Separate reply branches may therefore be represented by multiple Cases with the same `post_id` and `root_comment_id`. `case-find --case-id` resolves one Case, while a root-based lookup returns every matching candidate for explicit selection.

A non-null `reply_comment_id` from a supplied permalink is globally unique across Turns. Without that value, the deterministic identity is `case_id + parent_turn_id + direction + exact_text`; `parent_turn_id` is null for a root Turn. Mutable ordering or a “latest reply” is never identity.

`case-list-open` returns one row per Case with the latest public Turn's supplied exact URL. It never substitutes the Case root URL; when the latest Turn has no supplied URL, it returns `permalink_status: "missing"` and a null permalink. This ordering is presentation only and never identity. When sibling branches in one Case must be tracked independently, `case-split-branch` keeps the selected branch in a newly allocated Case, copies its shared ancestor path with fresh case-local Turn IDs, creates a verified backup, commits transactionally, and reads both graphs back. It refuses to copy a shared ancestor carrying a globally unique `reply_comment_id`.

## Dialogue workflows

- Intake: `$dialogue-lab-intake`
- Follow-up: `$dialogue-lab-followup`
- Posting confirmation: `$dialogue-lab-posting`
- Closeout: `$dialogue-lab-closeout`
- Strategy review: `$dialogue-lab-strategy-review`

Skills use read commands automatically. They may pass `--approved` only after the user approves the exact canonical write. No skill publishes to Facebook.

## Import and identity migration

1. Prepare a UTF-8 JSON snapshot with `cases` and `turns` arrays using the exact payload contract.
2. Initialize an empty outside-Git database.
3. Create a verified empty backup.
4. Run `db-import` once after explicit approval.
5. Run `check`, compare counts and representative records, create a populated backup, and record `docs/migration-receipt.json.example` with actual values.

Import is atomic and only accepts an empty database. Duplicate Case IDs, duplicate Turn identities, invalid enums, invalid URLs, missing parents, cycles, and foreign-key violations stop the transaction. Repeated `Post ID + Root Comment ID` values are allowed.

For an existing schema-version-1 database, `db-migrate-identity` first creates and verifies the approved outside-Git backup, then deterministically renumbers Cases by `(created_at, full existing case_id)` and rewrites every Case/Turn reference in one transaction. The full old ID is only a stable tie-breaker; its date and suffix are never parsed as identity. The command preserves schema version 1, commits, reopens the database, verifies the complete mapping and integrity, and emits a migration receipt. Any failure rolls back and blocks further writes until rollback and integrity are verified.

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
