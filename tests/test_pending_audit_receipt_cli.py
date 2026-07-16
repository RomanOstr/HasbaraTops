import json
from pathlib import Path

import pytest

from dialogue_lab.audit_log import append_audit_entry, value_hash, verify_audit_log
from dialogue_lab.cli import main
from dialogue_lab.errors import WriteSafetyError
from dialogue_lab.migration_receipt import migration_receipt_from_mapping
from dialogue_lab.models import TechnicalAuditEntry, to_jsonable
from dialogue_lab.pending_sync import (
    create_pending_sync,
    mark_reconciled,
    require_no_pending_sync,
)


def _audit_entry() -> TechnicalAuditEntry:
    expected = {"Case ID": "CASE-20260717-001", "Exact Text": "synthetic"}
    actual = dict(expected)
    return TechnicalAuditEntry(
        timestamp="2026-07-17T10:00:00+03:00",
        operation="append_turn",
        canonical_file_id="case-log-id",
        sheet="Turns",
        record_locator="CASE-20260717-001:T001",
        case_id="CASE-20260717-001",
        turn_id="T001",
        expected_value_hash=value_hash(expected),
        read_back_hash=value_hash(actual),
        verification_result=True,
        manual_version="2.7",
        manual_revision_state="manual-r1",
        schema_signature="a" * 64,
        git_commit="deadbeef",
    )


def test_failed_write_creates_complete_pending_sync_and_blocks_until_reconciled() -> None:
    record = create_pending_sync(
        operation="append_turn",
        target_file="case-log-id",
        target_sheet="Turns",
        case_id="CASE-20260717-001",
        turn_id="T001",
        expected_values={"Turn ID": "T001"},
        failure="read-back mismatch",
        last_verified_state={"row": "absent"},
        manual_version="2.7",
        source_revision_state={"manual": "r1", "case_log": "m1"},
        required_reconciliation_action="retry append and verify",
    )
    with pytest.raises(WriteSafetyError, match="unresolved"):
        require_no_pending_sync([record])
    require_no_pending_sync([mark_reconciled(record)])


def test_audit_log_contains_hashes_not_public_text_or_participant_names(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    entry = _audit_entry()
    append_audit_entry(path, entry)
    assert verify_audit_log(path) == 1
    text = path.read_text(encoding="utf-8")
    assert "synthetic" not in text
    assert "participant" not in text.lower()
    assert "profile" not in text.lower()


def test_migration_receipt_requires_manual_version_and_git_commit() -> None:
    payload: dict[str, object] = {
        "cutover_timestamp": "2026-07-17T10:00:00+03:00",
        "timezone": "Asia/Jerusalem",
        "manual_version": "2.7",
        "manual_revision_state": "r1",
        "case_log_schema_signature": "a" * 64,
        "case_log_modified_state": "m1",
        "repository_commit": "deadbeef",
        "repository_tag": "pre-codex-cutover",
        "codex_environment": "Codex app",
        "drive_connection_status": "read-only verified",
        "writer_enabled": False,
        "previous_writer_disabled": False,
        "test_results": "passed",
        "known_limitations": ["single writer"],
        "rollback_instructions": ["enable exactly one writer"],
    }
    receipt = migration_receipt_from_mapping(payload)
    serialized = to_jsonable(receipt)
    assert serialized["manual_version"] == "2.7"
    assert serialized["repository_commit"] == "deadbeef"


def test_cli_parse_url_and_version_emit_success(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["parse-url", "https://facebook.com/reel/123?comment_id=456"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["post_id"] == "123"
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0


def test_no_python_module_exposes_facebook_publishing_behavior() -> None:
    source_root = Path(__file__).parents[1] / "src" / "dialogue_lab"
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_root.glob("*.py"))
    assert "post_to_facebook" not in text
    assert "publish_to_facebook" not in text


def test_synthetic_eval_catalog_covers_required_scenarios() -> None:
    path = Path(__file__).parents[1] / "evals" / "cases" / "synthetic-cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    ids = {case["id"] for case in cases}
    assert len(cases) == 17
    assert {"new-case-intake", "failed-drive-write", "unsupported-manual-major"} <= ids
