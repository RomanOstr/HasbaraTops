# Israel Facebook Dialogue Lab — Codex Runtime

This repository is the non-canonical execution, validation, testing, and audit layer for the Israel Facebook Dialogue Lab. Google Drive remains the canonical source for workflow rules, case state, strategy findings, and factual material.

## Architecture

```text
Codex app / CLI / IDE
  ├─ AGENTS.md bootstrap
  ├─ .agents/skills workflow instructions
  ├─ dialogue-lab deterministic CLI
  ├─ synthetic tests and evals
  ├─ runtime-managed Google Drive connector boundary
  └─ local hash-only technical audit log
                    │
                    ▼
Google Drive — canonical source of truth
  ├─ 00 — Dialogue Lab Operating Manual
  ├─ 01 — Dialogue Lab Case Log
  ├─ 02 — Reply Strategy Guide
  └─ 03 — Israel Claims and Evidence Base
```

`General responses` is user-owned, protected, and non-canonical. The repository contains only its non-secret Drive ID and a deny-by-default policy. Canonical document bodies, Case Log exports, public Facebook text, backups, and credentials must not be committed.

The skills control model-driven workflows. Python controls identifiers, URL parsing, schemas, enums, lifecycle invariants, parent graphs, Pending Sync, source consistency, read-back comparison, audit hashes, and migration receipts. The Google Drive plugin is the external data boundary; it is runtime-managed and is not imported into Python.

## Installation

Python 3.12 or newer is supported.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install uv
uv sync --extra dev --frozen
uv run dialogue-lab --version
```

Run the checks:

```powershell
uv run pytest
uv run ruff check .
uv run mypy
uv run dialogue-lab doctor
```

Refresh the lock only after intentionally changing `pyproject.toml`:

```powershell
uv lock --upgrade
uv sync --extra dev --frozen
```

Optional local checks, when installed:

```powershell
pip-audit
gitleaks git --no-banner
```

## Codex setup

Codex reads the root `AGENTS.md` for repository bootstrap rules and discovers skills under `.agents/skills/`. Connect the Google Drive plugin in Codex, then copy `.codex/config.toml.example` to the environment-specific Codex configuration surface. The example contains no credentials and does not establish a connection by itself.

Read operations may run automatically. Case Log appends and updates require explicit user approval, a fresh source-consistency check, and targeted read-back. Delete, move, rename, sharing, autonomous Facebook posting, arbitrary Drive writes, and automatic edits to canonical documents are disabled.

## Live source startup

Before every case operation:

1. Read the complete live Operating Manual and record its Drive revision or modified state.
2. Run `dialogue-lab manual-version` and stop canonical write preparation on incompatibility.
3. Read current Case Log metadata, exact headers, Data Dictionary values/validations, and relevant rows.
4. Run `dialogue-lab schema-check` against a connector-derived schema JSON document.
5. Record the Case Log modified state and schema signature.
6. Load the Strategy Guide and Evidence Base only when the operation needs them; record their revision states.
7. Record the repository Git commit.

Never use a repository copy instead of a live canonical read.

## Operations

### New case intake

Invoke `$dialogue-lab-intake`. Parse every supplied URL, build `Post ID + Root Comment ID`, and search for duplicates before allocation. Immediately before allocation, re-read current Case IDs and unresolved Pending Sync records. An exploratory reply is not logged; only an explicitly approved or explicitly saved unposted reply may become an Outgoing Draft turn.

### Duplicate intake

When the identity already exists, do not allocate a new Case ID. Resolve the existing case and continue with `$dialogue-lab-followup`.

### Follow-up and branches

Invoke `$dialogue-lab-followup`. Append the exact incoming public turn, assign a case-local participant reference, resolve its direct parent, retain Parent Confidence, and validate the full parent graph. Multiple children may share a parent. Show a Thread Map for a branched Active Exchange.

### Posting confirmation

Invoke `$dialogue-lab-posting` only after the user confirms publication. Record the exact wording actually posted, even when it differs from an earlier recommendation. Preserve the supplied permalink and identifiers on the matching turn. The skill records state; it never posts to Facebook.

### Closure

Invoke `$dialogue-lab-closeout` only under a Manual-allowed closure condition. Record observable outcomes, the highest outcome score, What Worked, What Failed, and one Next Test. Do not infer persuasion from silence, deletion, blocking, a reaction, or disappearance.

### Strategy review

Invoke `$dialogue-lab-strategy-review` only on closed cases. Require at least three reasonably comparable cases and treat the first review at twenty closed cases as the first formal review. Report samples and confounders; do not infer causality from simple correlation. Propose Strategy Guide wording but never apply it without separate explicit approval.

### Pending Sync recovery

After a failed required write or mismatched read-back, construct a complete PENDING SYNC record in the interaction, create an audit failure entry, and do not claim that Drive changed. Reconcile or explicitly resolve it before allocating another Case ID.

### Source-consistency recovery

Record source states at operation start and compare them immediately before writing. If a relevant source changed, reload it, revalidate the operation, and regenerate any affected write. If compatibility cannot be established, stop the write and report the Manual and repository versions.

### Technical audit inspection

The default local path is `var/audit/dialogue-lab-audit.jsonl`. It stores hashes and operational metadata, not canonical content. Validate it with:

```powershell
uv run dialogue-lab audit-verify var/audit/dialogue-lab-audit.jsonl
```

Rotate by size outside Git: close the writer, rename the current JSONL with a timestamp suffix, create a new file on the next append, and retain files under the same local access controls. Audit logs are not recovery data.

## CLI

```text
dialogue-lab doctor
dialogue-lab parse-url <url>
dialogue-lab manual-version <text-or-file>
dialogue-lab schema-check <schema-json>
dialogue-lab source-consistency <json-file>
dialogue-lab case-key --post-id <id> --root-comment-id <id>
dialogue-lab next-case-id --date YYYY-MM-DD --existing <json-file>
dialogue-lab next-turn-id --case-id <id> --existing <json-file>
dialogue-lab validate-case <json-file>
dialogue-lab validate-turn <json-file>
dialogue-lab validate-transition <json-file>
dialogue-lab validate-parent-graph <json-file>
dialogue-lab pending-sync-check <json-file>
dialogue-lab verify-readback --expected <json-file> --actual <json-file>
dialogue-lab audit-verify <jsonl-file>
dialogue-lab migration-receipt <json-file>
```

Commands emit JSON and use non-zero exit status for validation failures. They do not print secrets and expose no Facebook publishing command.

## Connector boundary

`DriveProtocol` specifies semantic reads, Case Log writes, read-back, and revision-state operations. The live Google Drive plugin executes outside Python. Codex must translate a validated typed request into the narrow connector call and translate the response back into typed values. A local adapter is not presented as a live connector.

The initial writer is single-process and non-transactional. Immediately before allocating an ID, re-read rows, check duplicates and Pending Sync, calculate the next ID, verify revision state, write after approval, read back, compare, and audit. An optional future Apps Script or MCP gateway may make allocation atomic; see [connector boundary](docs/drive-connector-boundary.md).

## Version upgrades

- Manual version changes: read the new Manual, run compatibility checks, review behavior deltas, update repository compatibility only after evidence, and name the exact synchronized version.
- Case Log header changes: stop writes, inspect the live Data Dictionary and formulas, update header resolution and the schema signature, then rerun targeted tests.
- Enum changes: update enums, schema validation, lifecycle rules, fixtures, and CLI validation together.
- New canonical files: add only non-secret IDs and source-state handling; do not export content into Git.
- Repository compatibility changes: update `project.repository_version`, tests, and rollout receipt expectations in one change.

## Rollout and rollback

Follow [the controlled rollout](docs/rollout.md) and [rollback procedure](docs/rollback.md). The previous ChatGPT Project must become read-only reference after cutover; never leave two active writers. A receipt template is at [docs/migration-receipt.json.example](docs/migration-receipt.json.example).

Do not create cutover tags, named Drive versions, or offline backups during repository construction. Those are production state changes and require the documented gate and explicit approval.

## Limitations

- Initial single-writer mode does not provide atomic Google Sheets allocation.
- Python does not call the runtime-managed Google Drive connector directly.
- Every canonical write needs explicit human approval and connector read-back.
- No code publishes to Facebook.
- Local audit logs are non-canonical and cannot recover missing Case Log records.
- Parallel writers remain disabled until a narrow atomic gateway exists.
