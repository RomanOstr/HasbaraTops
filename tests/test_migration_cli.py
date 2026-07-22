import json
from pathlib import Path

import pytest

from dialogue_lab.cli import main
from dialogue_lab.migration_receipt import migration_receipt_from_mapping
from dialogue_lab.models import to_jsonable


def test_migration_receipt_requires_database_evidence_and_git_commit() -> None:
    payload: dict[str, object] = {
        "operation": "db-migrate-identity",
        "cutover_timestamp": "2026-07-20T10:00:00+03:00",
        "timezone": "Asia/Jerusalem",
        "database_schema_version_before": 1,
        "database_schema_version_after": 1,
        "database_integrity": "ok",
        "database_backup": "external/snapshot.sqlite3",
        "migrated_case_count": 1,
        "verified_turn_count": 2,
        "first_case_id": "Case-001",
        "last_case_id": "Case-001",
        "case_id_map": {"CASE-20260720-001": "Case-001"},
        "backup_verified": True,
        "committed_read_back": "verified",
        "repository_commit": "deadbeef",
        "test_results": "passed",
        "known_limitations": ["single local writer"],
        "rollback_instructions": ["restore the verified SQLite backup"],
    }
    receipt = migration_receipt_from_mapping(payload)
    serialized = to_jsonable(receipt)
    assert serialized["database_schema_version_after"] == 1
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


def test_synthetic_eval_catalog_covers_local_storage_scenarios() -> None:
    path = Path(__file__).parents[1] / "evals" / "cases" / "synthetic-cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    ids = {case["id"] for case in cases}
    assert len(cases) == 29
    assert {
        "new-case-intake",
        "same-root-separate-cases",
        "reply-comment-turn-duplicate",
        "identity-migration-readback",
        "sqlite-write-rollback",
        "schema-version-mismatch",
    } <= ids
