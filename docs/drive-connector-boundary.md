# Google Drive connector boundary

The Codex runtime owns Google Drive authentication and connector invocation. Python owns deterministic request validation and response verification. Do not place OAuth credentials, cookies, service-account keys, or provider internals in this repository.

## Required semantic operations

Reads: `read_operating_manual`, `read_strategy_guide`, `read_evidence_base`, `read_case_log_schema`, `read_case_rows`, `read_turn_rows`, `find_case_by_identity`, `find_unresolved_pending_sync`, and `read_file_revision_state`.

Approval-gated Case Log writes: `append_case`, `update_case`, `append_turn`, and `update_turn`.

Verification reads: `read_back_case` and `read_back_turn`.

The runtime must validate a `DriveWriteRequest`, recheck source state, execute one narrow connector call, perform a targeted read-back, and run deterministic comparison. Connector acknowledgement is not success.

## Optional atomic gateway

A future Apps Script or MCP gateway may expose only `findCaseByIdentity`, `allocateCase`, `appendCase`, `appendTurn`, `updateTurn`, `recordPostedReply`, `updateCaseStatus`, `closeCase`, and `readCanonicalDocument`.

It must provide atomic identifier allocation, exact schema validation, source-revision checks, single-purpose methods, read-back responses, and actionable errors. It must expose no generic spreadsheet writer, `General responses` access, credential output, or Facebook publishing.
