## Instruction enforcement

- All instruction bullets in this file are mandatory, blocking, and
  closure-gating for the phase, action, decision, artifact, or response they
  govern.
- Do not proceed with or claim completion for any action, decision, artifact, or
  response when an applicable instruction bullet is unmet, unverifiable, or in
  conflict; report the blocker or conflict instead.


## HasbaraTops

- [HASBARA-CHECK-01] Run `dialogue-lab check` before a canonical write, after a failed write or readiness check, or when database state is uncertain; ordinary read-only queries must reuse fresh sufficient evidence.
- [HASBARA-CANONICAL-01] Treat repository Markdown as canonical governance, strategy, and evidence content and the configured SQLite database as canonical Case and Turn state; do not use MCP for Dialogue Lab work.
- [HASBARA-IDENTITY-01] Use `config/storage.toml`; preserve the SQLite schema version; treat Case ID as definitive, allow multiple Cases per `Post ID + Root Comment ID`, and treat root lookup as candidate discovery only.
- [HASBARA-IDENTITY-02] Deduplicate Turns by supplied `reply_comment_id`; when absent, use Case ID + Parent Turn ID (including null roots) + Direction + Exact Text; never use mutable latest-reply state as identity.
  - limits: HASBARA-OPEN-CASES-01
- [HASBARA-OPEN-CASES-01] When presenting open Cases, use each Case's latest public Turn supplied exact URL; never substitute the Case root URL, and mark a missing link explicitly.
- Invoke the matching Dialogue Lab skill for intake, follow-up, posting confirmation, closeout, or strategy review.
- [DL-REPLY-01] When proposing a public Dialogue Lab reply, provide one
  complete, self-contained, ready-to-post response
  - limits: OUT-03
- Never edit, move, rename, replace, delete, import, or summarize `General responses` without the user's explicit instruction for that exact action.
- Perform canonical writes only through explicit-approval `dialogue-lab` commands that use SQLite transactions and committed read-back verification.
- After a failed canonical write, verify rollback and database integrity; block further writes while either remains unresolved.
- Never open, inspect, click, scroll, or otherwise interact with Facebook unless the user explicitly asks. Never post to Facebook autonomously. Never commit SQLite databases, exports, backups, credentials, or secrets.

### Repo checkout and worktrees:

- The primary skills repo checkout used to generate installed HasbaraTops skill
  copies must stay either on local `main` tracking `origin/main` or on a local
  `release/*` branch created from `main` for an active unpublished batch.
- Do not develop or patch HasbaraTops skill source directly in the skills repo
  checkout during create, update, audit, or repair work; for any task that
  modifies skills, work in one thread-owned git worktree, name that worktree
  after the thread rather than a subtask, reuse it for follow-on skill changes
  in the same thread unless conflicting branch histories or explicit user
  direction require a new one, and do not place it inside the skills repo
  checkout.
- Keep installed HasbaraTops skill folders generated from the skills repo checkout
  path, not from task worktrees. For local preview of unpublished batches,
  refresh remote refs with `git fetch --prune origin`, then merge ready worktree
  branches into the skills repo checkout's local `release/*` branch and rerun
  `skills/ceratops-skill-lifecycle/scripts/runtime/install-managed-skills.ps1`
  instead of generating installed skills from task worktrees.
- Do not stage skill-source changes into a local `release/*` batch unless the
  task explicitly requests staging, shipping, or local preview sync.
- Skills-repo changes must ship from `release/*`, never directly from task or
  feature branches.
- New HasbaraTops skill creation is the only default-staging exception:
  `$ceratops-skill-lifecycle` create must finish with change-promotion and
  install verification unless the user opts out.
- For staging or shipping, use `$ceratops-skill-lifecycle` change-promotion or
  ship-to-remote. After shipping, restore the checkout from `origin/main`,
  reinstall managed skills from `main`, and report retained worktrees or release
  branches.

### Instruction and skill maintenance:

- Before proposing or editing `AGENTS.md`, `automation.toml`, `SKILL.md`, shared
  skill sections, skill manifests, or helper-contract text, re-open the relevant
  files from disk and use the current contents as the source of truth.
- Treat recommendations about instruction, automation, skill, and
  helper-contract changes as advisory unless the user explicitly asks to apply a
  named change.
- In repo-tracked files intended for public sharing or GitHub, including
  repo-tracked `AGENTS.md`, `automation.toml`, `SKILL.md`, generated runtime
  skill files, scripts, docs, and examples, do not hardcode user-local absolute
  filesystem paths unless an external runtime explicitly requires them; use
  repo-relative paths or portable variables such as `$CODEX_HOME`.
- For skill runtime workflows, invoke shared helpers through installed console
  commands, `python -m <module>` entrypoints, or scripts copied into the
  installed skill folder; do not locate shared helpers by absolute paths or by
  the repo's parent directory.
- When a workflow needs a shared repo-maintenance script, run `scripts/<name>`
  from the active source checkout root when available, otherwise from the
  installed skill folder; when a helper is skill-local, run it from that skill
  folder or the corresponding source skill folder; stop as blocked if neither
  declared location contains it.
- Prefer concise, principle-based, machine-oriented wording; avoid example lists
  unless the examples are needed to disambiguate behavior.
- After instruction edits, verify the changed diff or reopened section and
  confirm no new duplicate, contradiction, or dropped behavior was introduced.
- When an automation uses a script or helper, compare prompt and code before
  finishing and keep outcome, blocker, cleanup, alert, and memory paths aligned.
- Put deterministic, testable, or procedural automation behavior in scripts or
  helpers rather than prompt text when such helpers exist.
- When updating an automation, skill, instruction, or related helper script,
  assess whether the change could materially increase recurring or avoidable
  credit usage; if so, report that before treating the update as done.
