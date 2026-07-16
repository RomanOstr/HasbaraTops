# Israel Facebook Dialogue Lab

- Before case work, read the live Operating Manual through the configured Drive ID, verify that its version is supported, and record the revision state used.
- Treat Google Drive as canonical and repository files as non-canonical implementation; never use or commit repository exports as substitutes for live canonical sources.
- Use `config/drive-files.toml`, preserve the live Case Log schema, and check `Post ID + Root Comment ID` for duplicates before allocating a Case ID.
- Invoke the matching Dialogue Lab skill for intake, follow-up, posting confirmation, closeout, or strategy review.
- Never edit, move, rename, replace, delete, import, or summarize `General responses` without the user's explicit instruction for that exact action.
- Before a canonical write, verify that relevant source state has not materially changed; require explicit approval, read the record back, and compare every expected field.
- After a failed required write, follow the Manual's Recovery procedure and block new Case ID allocation while any `PENDING SYNC` is unresolved.
- Never post to Facebook autonomously. Never store credentials, OAuth material, secrets, or canonical document bodies in Git.
